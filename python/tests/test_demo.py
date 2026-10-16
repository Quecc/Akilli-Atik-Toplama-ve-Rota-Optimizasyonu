"""Python çekirdeğinin ve yerel HTTP uçlarının doğrulama testleri."""

import json
import math
from pathlib import Path
import shutil
import subprocess
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from temiz_rota.graph import Network, RoutingError, build_graph, dijkstra, haversine
from temiz_rota.routing import plan_tour
from temiz_rota.sensor import Calibration, MeasurementError, is_collection_candidate, parse_distance
from temiz_rota.server import make_server
from temiz_rota.service import PROJECT_ROOT, Planner


class SensorTests(unittest.TestCase):
    def test_empty_full_and_intermediate(self):
        calibration = Calibration()
        self.assertEqual(calibration.fill_percent(200), 0)
        self.assertEqual(calibration.fill_percent(20), 100)
        self.assertAlmostEqual(calibration.fill_percent(80), 66.6666667, places=5)

    def test_clipping_is_only_for_valid_measurements(self):
        self.assertEqual(Calibration().fill_percent(300), 0)
        self.assertEqual(Calibration().fill_percent(10), 100)
        for value in [0, -1, 401, math.nan, math.inf, True, "80", None]:
            with self.subTest(value=value), self.assertRaises(MeasurementError):
                Calibration().fill_percent(value)

    def test_invalid_calibration(self):
        for empty, full in [(20, 200), (20, 20), (401, 20), (200, 0), (True, 20)]:
            with self.subTest(empty=empty, full=full), self.assertRaises(ValueError):
                Calibration(empty_cm=empty, full_cm=full)

    def test_numeric_comma_and_serial_line(self):
        self.assertEqual(parse_distance("80,5"), 80.5)
        self.assertEqual(parse_distance(80), 80)
        self.assertEqual(parse_distance("Mesafe: 119.7 cm | Yaklasik doluluk: %44.6"), 119.7)

    def test_bad_unit_and_unreadable_data(self):
        for value in ["", "abc", "80 in", "%70", "NaN", "-1", "401", None]:
            with self.subTest(value=value), self.assertRaises(MeasurementError):
                parse_distance(value)

    def test_strict_threshold(self):
        self.assertFalse(is_collection_candidate(50, 50))
        self.assertTrue(is_collection_candidate(50.01, 50))
        self.assertFalse(is_collection_candidate(100, 100))

    def test_threshold_validation(self):
        for value in [-1, 101, math.nan, True]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                is_collection_candidate(80, value)


class GraphAndRoutingTests(unittest.TestCase):
    def test_haversine_identity_and_known_scale(self):
        self.assertEqual(haversine((0, 0), (0, 0)), 0)
        self.assertAlmostEqual(haversine((0, 0), (0, 1)), 111194.9266, places=3)

    def test_oneway_and_reverse_oneway(self):
        graph = build_graph({"nodes": {"1": [39, 32], "2": [39, 32.001], "3": [39, 32.002]},
                             "roads": [{"nodes": [1, 2], "oneway": "yes"}, {"nodes": [2, 3], "oneway": "-1"}]})
        self.assertEqual([n for n, _ in graph[1]], [2])
        self.assertEqual(graph[2], [])
        self.assertEqual([n for n, _ in graph[3]], [2])

    def test_dijkstra_finds_a_cheaper_indirect_path(self):
        distances, previous = dijkstra({1: [(2, 20), (3, 2)], 2: [], 3: [(2, 3)]}, 1, {2})
        self.assertEqual(distances[2], 5)
        self.assertEqual(previous[2], 3)

    def test_unreachable_and_negative_edges_raise(self):
        with self.assertRaises(RoutingError):
            dijkstra({1: [], 2: []}, 1, {2})
        with self.assertRaises(RoutingError):
            dijkstra({1: [(2, -1)], 2: []}, 1, {2})

    def test_empty_single_and_asymmetric_tours(self):
        matrix = [[0, 3, 8], [20, 0, 2], [4, 15, 0]]
        self.assertEqual(plan_tour(matrix, []).order, (0,))
        self.assertEqual(plan_tour(matrix, [1]).meters, 23)
        result = plan_tour(matrix, [1, 2])
        self.assertEqual(result.order, (0, 1, 2, 0))
        self.assertEqual(result.meters, 9)

    def test_invalid_matrix_or_index(self):
        for matrix, ids in [([], []), ([[0, 1]], [1]), ([[0, math.inf], [1, 0]], [1]), ([[0, 1], [1, 0]], [2])]:
            with self.subTest(matrix=matrix), self.assertRaises(RoutingError):
                plan_tour(matrix, ids)


class PlannerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.planner = Planner()

    def test_initial_14_of_20_and_no_duplicate_visits(self):
        result = self.planner.plan()
        self.assertEqual(len(result["candidateIds"]), 14)
        self.assertEqual(len(result["skippedIds"]), 6)
        order = result["tour"]["order"]
        self.assertEqual(order[0], 0)
        self.assertEqual(order[-1], 0)
        self.assertEqual(len(set(order[1:-1])), 14)
        self.assertLessEqual(result["tour"]["meters"], result["baseline"]["meters"] + 0.001)

    def test_all_441_point_paths_follow_existing_directed_edges(self):
        network = self.planner.network
        for i, start in enumerate(network.points):
            for j, end in enumerate(network.points):
                route = network.paths[i][j]
                self.assertEqual((route[0], route[-1]), (start, end))
                length = 0.0
                for a, b in zip(route, route[1:]):
                    lengths = [m for n, m in network.graph[a] if n == b]
                    self.assertTrue(lengths)
                    length += min(lengths)
                self.assertAlmostEqual(length, network.matrix[i][j], places=5)

    def test_all_empty_and_all_full(self):
        empty = [{"id": identifier, "fill": 0} for identifier in self.planner.ids]
        full = [{"id": identifier, "fill": 100} for identifier in self.planner.ids]
        result = self.planner.plan(empty)
        self.assertEqual(result["tour"]["meters"], 0)
        self.assertEqual(result["tour"]["pathNodes"], [])
        result = self.planner.plan(full)
        self.assertEqual(len(result["candidateIds"]), 20)
        self.assertAlmostEqual(result["tour"]["meters"], result["baseline"]["meters"], places=5)

    def test_bad_bin_list_is_not_silently_treated_as_empty(self):
        for bins in [[], {}, [{"id": "K01", "fill": 50}] * 20, [{"id": identifier, "fill": math.nan} for identifier in self.planner.ids]]:
            with self.subTest(bins_type=type(bins)), self.assertRaises(ValueError):
                self.planner.plan(bins)

    def test_measurement_changes_only_selected_bin(self):
        bins = self.planner.initial_bins()
        bins[2]["fill"] = self.planner.measurement("80")["fillPercent"]
        self.assertEqual(len(self.planner.plan(bins)["candidateIds"]), 15)
        self.assertEqual(self.planner.initial_bins()[2]["fill"], 34)

    @unittest.skipUnless(shutil.which("node"), "JavaScript karşılaştırması için Node.js gerekir; Python çekirdeği bundan bağımsızdır.")
    def test_javascript_and_python_use_same_data_and_agree(self):
        script = "const E=require('./route-engine.js'),fs=require('fs'),d=JSON.parse(fs.readFileSync('data/map-data.json','utf8'));const js=JSON.parse(fs.readFileSync('data/map-data.js','utf8').split('=').slice(1).join('=').trim().replace(/;$/,''));if(JSON.stringify(js)!==JSON.stringify(d))throw Error('data mismatch');const n=E.makeNetwork(d),b=E.planTour(n.matrix,d.bins.map((_,i)=>i+1)),t=E.planTour(n.matrix,d.bins.flatMap((x,i)=>x.fill>50?[i+1]:[]),b.order);console.log(JSON.stringify({baseline:b.meters,tour:t.meters}));"
        result = subprocess.run([shutil.which("node"), "-e", script], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True)
        javascript = json.loads(result.stdout)
        python = self.planner.plan()
        self.assertAlmostEqual(javascript["baseline"], python["baseline"]["meters"], places=3)
        self.assertAlmostEqual(javascript["tour"], python["tour"]["meters"], places=3)


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.planner = Planner()
        cls.server = make_server(0, cls.planner)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request(self, endpoint, payload=None, origin=None):
        headers = {"Content-Type": "application/json"}
        if origin:
            headers["Origin"] = origin
        body = None if payload is None else json.dumps(payload).encode()
        return urlopen(Request(self.url + endpoint, data=body, headers=headers), timeout=10)

    def test_health_and_static_page(self):
        with self.request("/api/health") as response:
            self.assertEqual(json.load(response)["engine"], "python")
        with self.request("/") as response:
            self.assertIn(b"Temiz Rota", response.read())

    def test_measurement_and_route_api(self):
        with self.request("/api/measurement", {"measurement": "80,0"}) as response:
            self.assertAlmostEqual(json.load(response)["fillPercent"], 66.6666667, places=5)
        with self.request("/api/plan", {"bins": self.planner.initial_bins(), "threshold": 50}) as response:
            self.assertEqual(len(json.load(response)["candidateIds"]), 14)

    def test_invalid_measurement_and_missing_bins_are_400(self):
        for endpoint, payload in [("/api/measurement", {"measurement": "wrong"}), ("/api/plan", {})]:
            with self.subTest(endpoint=endpoint), self.assertRaises(HTTPError) as error:
                self.request(endpoint, payload)
            self.assertEqual(error.exception.code, 400)

    def test_external_origin_is_403(self):
        with self.assertRaises(HTTPError) as error:
            self.request("/api/measurement", {"measurement": 80}, "https://example.com")
        self.assertEqual(error.exception.code, 403)

    def test_hidden_or_outside_files_are_not_served(self):
        for path in ["/.git/config", "/%2e%2e/README.md"]:
            for method in ["GET", "HEAD"]:
                with self.subTest(path=path, method=method), self.assertRaises(HTTPError) as error:
                    urlopen(Request(self.url + path, method=method), timeout=10)
                self.assertEqual(error.exception.code, 403)


if __name__ == "__main__":
    unittest.main()
