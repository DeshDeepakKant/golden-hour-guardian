PY ?= .venv/bin/python
PIP ?= .venv/bin/pip

.PHONY: venv install seed run test test-fast sim reset android demo bench check

venv:
	python3 -m venv .venv

install: venv
	$(PIP) install -q -r requirements.txt

seed:
	$(PY) -m mocks.seed --reset

run:
	$(PY) -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

test:
	$(PY) -m pytest -q

test-fast:
	$(PY) -m pytest -q -x --ff

# usage: make sim s=ato   (ato | genuine | inbound | noresponse | injection)
sim:
	curl -s -X POST http://127.0.0.1:8000/sim/scenario/$(s) | $(PY) -m json.tool

reset:
	curl -s -X POST http://127.0.0.1:8000/sim/reset | $(PY) -m json.tool

android:
	bash scripts/android.sh

demo:
	bash scripts/demo.sh

bench:
	$(PY) -m scripts.bench_llm

check:
	$(PY) -c "import app.contracts as c; print('contracts ok:', len(c.Action), 'actions')"
