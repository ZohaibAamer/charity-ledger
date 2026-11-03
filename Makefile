.PHONY: install extract build test lint format quality dashboard clean

install:  ## Install the package with all extras
	pip install -e ".[dev,snowflake,azure,aws]"

extract:  ## Run all source extractions
	python -m extract.run_all

build:  ## Run dbt models and tests
	cd dbt_project && dbt deps && dbt build --profiles-dir .

quality:  ## Print the data quality report
	cd dbt_project && dbt run-operation generate_data_quality_report --profiles-dir .

lint:  ## Lint Python and SQL
	ruff check extract/
	sqlfluff lint dbt_project/models

format:  ## Format Python and SQL in place
	ruff format extract/
	ruff check --fix extract/
	sqlfluff fix dbt_project/models

dashboard:  ## Start the Evidence.dev dev server
	cd evidence && npm install && npm run dev

clean:  ## Remove build artifacts and caches
	rm -rf dbt_project/target dbt_project/dbt_packages dbt_project/logs
	find . -type d -name __pycache__ -exec rm -rf {} +
