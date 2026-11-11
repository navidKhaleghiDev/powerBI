"""Governed starter definitions. Source mappings are deliberately never guessed."""

TEMPLATES = [
    {
        "key": key,
        "title": title,
        "description": description,
        "aggregation": "sum",
        "field": "amount",
        "filters": filters,
        "dimensions": ["day", "month", "year", *dimensions],
    }
    for key, title, description, filters, dimensions in [
        (
            "income",
            "Recognized income",
            "Sum of approved recognized income, excluding tax. Map recognition entries, not payment receipts.",
            {},
            ["incomeType", "paymentTerms"],
        ),
        (
            "formalIncome",
            "Formal income",
            "Recognized income classified as formal.",
            {"incomeType": ["formal"]},
            ["incomeType", "paymentTerms"],
        ),
        (
            "informalIncome",
            "Informal income",
            "Recognized income classified as informal.",
            {"incomeType": ["informal"]},
            ["incomeType", "paymentTerms"],
        ),
        (
            "cashIncome",
            "Cash-term income",
            "Recognized income from cash sales terms; this does not establish receipt of payment.",
            {"paymentTerms": ["cash"]},
            ["incomeType", "paymentTerms"],
        ),
        (
            "creditIncome",
            "Credit-term income",
            "Recognized income from credit sales terms.",
            {"paymentTerms": ["credit"]},
            ["incomeType", "paymentTerms"],
        ),
        (
            "expenses",
            "Recognized expenses",
            "Sum of approved expense recognition entries. Purchases are not automatically expenses.",
            {},
            [],
        ),
        (
            "purchases",
            "Approved purchases",
            "Sum of approved purchase entries; excludes unapproved records through the business source view.",
            {},
            [],
        ),
        (
            "incomeReturns",
            "Income returns",
            "Sum of approved income return entries using the documented sign convention.",
            {},
            [],
        ),
        (
            "expenseReturns",
            "Expense returns",
            "Sum of approved expense return entries using the documented sign convention.",
            {},
            [],
        ),
    ]
]
