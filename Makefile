.PHONY: api web test demo install

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

api:
	cd backend && PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

web:
	cd frontend && npm run dev -- --host 0.0.0.0 --port 5173

test:
	cd backend && PYTHONPATH=. python3 -m pytest tests -q

demo:
	./scripts/run-demo.sh
