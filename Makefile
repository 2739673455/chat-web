.PHONY: init_db app test

init_db:
	uv run app/utils/_init_db.py
app:
	uv run -m app.main
test:
	uv run pytest