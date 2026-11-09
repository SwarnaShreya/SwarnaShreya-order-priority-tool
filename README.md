# Bakery Order Priority Tool

A learning project that allocates limited ingredients to customer orders.

## Features

- Enter available flour, butter, and sugar.
- Add, edit, or delete orders.
- Prioritize by earliest deadline or highest profit per order.
- View allocations, shortages, remaining stock, and total profit.
- Download the allocation plan as a CSV.

## Run locally

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Start the app:

```bash
python -m streamlit run app.py
```

## Limitations

Uses fictional recipes and allocates complete orders only.
Does not consider production capacity or ingredient delivery times.
Highest-profit-first ranking does not guarantee maximum total profit.
