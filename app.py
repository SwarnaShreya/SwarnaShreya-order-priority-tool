import pandas as pd
import streamlit as st

st.title("Bakery Order Priority Tool")
st.write("Decide which orders to allocate limited ingredients to.")
st.caption(
    "Learning demo: fictional recipes, complete orders only, "
    "and no oven or staffing capacity checks."
)

# 1. Available ingredients
st.subheader("1. Available ingredients")

stock = {
    "Flour": st.number_input(
        "Flour (grams)", min_value=0, value=1000
    ),
    "Butter": st.number_input(
        "Butter (grams)", min_value=0, value=500
    ),
    "Sugar": st.number_input(
        "Sugar (grams)", min_value=0, value=500
    ),
}

# 2. Recipes: grams needed per finished item
recipes = {
    "Cookie": {"Flour": 20, "Butter": 10, "Sugar": 10},
    "Brownie": {"Flour": 15, "Butter": 20, "Sugar": 15},
}

st.subheader("2. Sample recipes")
st.write("Grams needed per item:")
st.dataframe(pd.DataFrame(recipes).T)

# 3. Sample orders
sample_orders = pd.DataFrame([
    {
        "Order": "A",
        "Product": "Cookie",
        "Quantity": 20,
        "Due in hours": 2,
        "Profit per order ($)": 30.0,
    },
    {
        "Order": "B",
        "Product": "Brownie",
        "Quantity": 20,
        "Due in hours": 4,
        "Profit per order ($)": 50.0,
    },
    {
        "Order": "C",
        "Product": "Cookie",
        "Quantity": 10,
        "Due in hours": 6,
        "Profit per order ($)": 15.0,
    },
])

st.subheader("3. Customer orders")
st.write("Edit orders or add a new row at the bottom.")
st.caption(
    "Enter total profit for the complete order, not profit per item. "
    "If you change quantity, update the order's profit too."
)

orders = st.data_editor(
    sample_orders,
    hide_index=True,
    num_rows="dynamic",
    column_config={
        "Order": st.column_config.TextColumn(
            required=True,
        ),
        "Product": st.column_config.SelectboxColumn(
            options=list(recipes.keys()),
            required=True,
        ),
        "Quantity": st.column_config.NumberColumn(
            min_value=1,
            step=1,
            default=1,
            required=True,
        ),
        "Due in hours": st.column_config.NumberColumn(
            min_value=0,
            step=1,
            default=1,
            required=True,
        ),
        "Profit per order ($)": st.column_config.NumberColumn(
            min_value=0.0,
            step=1.0,
            default=0.0,
            required=True,
        ),
    },
    key="orders_editor",
)

# Choose the allocation rule.
priority_rule = st.selectbox(
    "How should orders be prioritized?",
    ["Earliest deadline first", "Highest profit first"],
)

st.caption(
    "Highest profit first ranks individual orders. "
    "It does not guarantee the highest possible total profit."
)

if st.button("Prioritize orders"):
    orders = orders.copy()

    # Validate order inputs.
    if orders.empty:
        st.warning("Add at least one order.")
        st.stop()

    if orders.isna().any().any():
        st.warning("Fill in every field before prioritizing.")
        st.stop()

    orders["Order"] = orders["Order"].astype(str).str.strip()

    if (
        orders["Order"].eq("").any()
        or orders["Order"].duplicated().any()
    ):
        st.warning("Give each order a unique, non-empty order ID.")
        st.stop()

    if not orders["Product"].isin(recipes.keys()).all():
        st.warning("Choose Cookie or Brownie for every order.")
        st.stop()

    for column, minimum in [
        ("Quantity", 1),
        ("Due in hours", 0),
    ]:
        values = pd.to_numeric(orders[column], errors="coerce")

        if (
            values.isna().any()
            or (values < minimum).any()
            or (values == float("inf")).any()
            or (values % 1 != 0).any()
        ):
            st.warning(
                f"{column} must contain whole numbers "
                f"of {minimum} or more."
            )
            st.stop()

        orders[column] = values.astype(int)

    profits = pd.to_numeric(
        orders["Profit per order ($)"], errors="coerce"
    )

    if (
        profits.isna().any()
        or (profits < 0).any()
        or (profits == float("inf")).any()
    ):
        st.warning("Enter a valid, non-negative profit for each order.")
        st.stop()

    orders["Profit per order ($)"] = profits

    # Sort orders by the selected rule.
    # Equal priorities keep the original table order.
    if priority_rule == "Highest profit first":
        sorted_orders = orders.sort_values(
            ["Profit per order ($)", "Due in hours"],
            ascending=[False, True],
            kind="stable",
        )
    else:
        sorted_orders = orders.sort_values(
            "Due in hours", kind="stable"
        )

    remaining = stock.copy()
    results = []
    total_profit = 0.0

    # Allocate ingredients to complete orders.
    for _, order in sorted_orders.iterrows():
        recipe = recipes[order["Product"]]

        needed = {
            ingredient: grams * order["Quantity"]
            for ingredient, grams in recipe.items()
        }

        shortages = {
            ingredient: amount - remaining[ingredient]
            for ingredient, amount in needed.items()
            if amount > remaining[ingredient]
        }

        if not shortages:
            for ingredient, amount in needed.items():
                remaining[ingredient] -= amount

            status = "Allocate"
            reason = "Enough ingredients at this priority."
            total_profit += float(order["Profit per order ($)"])
        else:
            status = "Wait"
            reason = "Short by: " + ", ".join(
                f"{amount} g {ingredient}"
                for ingredient, amount in shortages.items()
            )

        results.append({
            "Order": order["Order"],
            "Product": order["Product"],
            "Quantity": order["Quantity"],
            "Due in hours": order["Due in hours"],
            "Profit per order ($)": order["Profit per order ($)"],
            "Decision": status,
            "Reason": reason,
        })

    # Display the plan.
    allocation = pd.DataFrame(results)

    st.subheader("4. Recommended allocation")
    st.write(f"Priority rule: **{priority_rule}**")
    st.metric(
        "Profit from allocated orders",
        f"${total_profit:,.2f}",
    )
    st.dataframe(allocation, hide_index=True)

    st.subheader("5. Ingredients remaining")
    st.dataframe(
        pd.DataFrame(
            remaining.items(),
            columns=["Ingredient", "Grams remaining"],
        ),
        hide_index=True,
    )

    # Download results without rerunning the app.
    export = allocation.copy()
    export["Priority rule"] = priority_rule

    st.download_button(
        label="Download allocation plan",
        data=export.to_csv(index=False).encode("utf-8"),
        file_name="allocation_plan.csv",
        mime="text/csv",
        on_click="ignore",
    )