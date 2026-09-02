# محرّك أسلوط — أوامر التشغيل الشائعة
.PHONY: help install all test lint clean

help:
	@echo "make install   تثبيتٌ قابلٌ للتحرير + أدوات التطوير"
	@echo "make all       تشغيل السلسلة الخماسية كاملةً"
	@echo "make test      pytest"
	@echo "make lint      ruff"
	@echo "make clean     حذف مخرجات الجولات و__pycache__"

install:
	python3 -m pip install -e ".[dev]"

all:
	python3 -m aslot all

test:
	python3 -m pytest

lint:
	python3 -m ruff check src tests

clean:
	rm -rf reports/ .pytest_cache/
	find . -name __pycache__ -type d -exec rm -rf {} +
