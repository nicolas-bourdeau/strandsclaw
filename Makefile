.PHONY: help sync bootstrap test list-skills show-config run clean

UV ?= uv
APP ?= strandsclaw
CMD ?= show-config

help: ## Show available commands
	@echo "StrandsClaw Make Targets"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'

sync: ## Install/update dependencies from pyproject.toml
	$(UV) sync

bootstrap: ## Initialize runtime directories (.state, skills)
	$(UV) run $(APP) bootstrap

test: ## Run test suite
	$(UV) run pytest

list-skills: ## List discovered local skills
	$(UV) run $(APP) list-skills

show-config: ## Print resolved runtime configuration
	$(UV) run $(APP) show-config

run: ## Run CLI subcommand via CMD, e.g. `make run CMD=list-skills`
	$(UV) run $(APP) $(CMD)

clean: ## Remove generated caches and build artifacts
	rm -rf .pytest_cache .mypy_cache .ruff_cache build dist *.egg-info
