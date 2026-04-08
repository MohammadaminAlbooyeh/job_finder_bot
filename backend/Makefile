VENV_DIR := .venv
PYTHON := python3

.PHONY: venv activate

venv:
	@echo "Creating virtualenv in $(VENV_DIR)"
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Installing requirements..."
	. $(VENV_DIR)/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

activate:
	@echo "To activate run: source $(VENV_DIR)/bin/activate"
