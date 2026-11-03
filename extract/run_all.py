"""Run all extractors in sequence."""
from extract import charity_commission, companies_house, grantnav


def main():
    print("=" * 60)
    print("CHARITY LEDGER - EXTRACTION PIPELINE")
    print("=" * 60)

    print("\n[1/3] Charity Commission")
    charity_commission.run()

    print("\n[2/3] Companies House")
    companies_house.run()

    print("\n[3/3] 360Giving GrantNav")
    grantnav.run()

    print("\n" + "=" * 60)
    print("All extractions complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
