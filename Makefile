# Three targets. `make check` is what CI runs.
.PHONY: check build serve

check: ## Build the site and fail on any warning
	npm run check

build: ## Build the site into build/site
	npm run build

serve: build ## Build and serve locally on http://localhost:5000
	npm run serve

tables: ## Re-render the routes, authorization and events tables of every feature page from scripts/openapi.json
	python3 scripts/feature-tables.py scripts/openapi.json ../platformkit
