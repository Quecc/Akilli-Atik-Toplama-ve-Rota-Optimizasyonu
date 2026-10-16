"""Örnek senaryoyu terminalden çalıştır ve sonucu JSON olarak kaydet."""

import argparse
import json
from pathlib import Path
from temiz_rota.service import Planner


def main() -> None:
    parser = argparse.ArgumentParser(description="Temiz Rota — terminal demosu")
    parser.add_argument(
        "--threshold", type=float, default=50, help="Toplama eşiği, yüzde"
    )
    parser.add_argument(
        "--distance", help="Örnek kutuya uygulanacak cm veya Tinkercad satırı"
    )
    parser.add_argument("--bin", default="K03", help="Ölçüm uygulanacak örnek kutu")
    parser.add_argument("--output", type=Path, help="Sonucu ayrıca JSON dosyasına yaz")
    args = parser.parse_args()
    planner = Planner()
    bins = planner.initial_bins()
    try:
        if args.distance is not None:
            if args.bin not in planner.ids:
                parser.error("Kutu kimliği bulunamadı.")
            measurement = planner.measurement(args.distance)
            for bin_data in bins:
                if bin_data["id"] == args.bin:
                    bin_data["fill"] = measurement["fillPercent"]
                    break
        report = planner.plan(bins, args.threshold)
    except ValueError as error:
        parser.error(str(error))
    text = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
