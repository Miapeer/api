from sqlmodel import text

from miapeer.adapter import sql

GET_ALL = text(
    """
    with
        recent_transactions as (
            select
                t.transaction_id,
                substr(cast(coalesce(t.clear_date, t.transaction_date) as varchar), 1, 7) as report_date,
                t.category_id,
                t.amount
            from quantum_transaction t
                inner join quantum_budget b
                    on b.category_id = t.category_id
                inner join quantum_account a
                    on a.account_id = t.account_id
                inner join quantum_portfolio p
                    on p.portfolio_id = a.portfolio_id
                inner join quantum_portfolio_user pu
                    on pu.portfolio_id = p.portfolio_id
            where
                pu.user_id = :user_id and
                (clear_date is null or clear_date >= :limit_date)
        ),
        older_transactions as (
            select
                t.transaction_id,
                substr(cast(t.clear_date as varchar), 1, 7) as report_date,
                t.category_id,
                t.amount
            from quantum_transaction t
                inner join quantum_budget b
                    on b.category_id = t.category_id
                inner join quantum_account a
                    on a.account_id = t.account_id
                inner join quantum_portfolio p
                    on p.portfolio_id = a.portfolio_id
                inner join quantum_portfolio_user pu
                    on pu.portfolio_id = p.portfolio_id
                left join recent_transactions rt
                    on rt.transaction_id = t.transaction_id
            where
                pu.user_id = :user_id and
                clear_date >= :limit_date and
                rt.transaction_id is null
        ),
        transactions as (
            select report_date, category_id, amount
            from older_transactions

            union all

            select report_date, category_id, amount
            from recent_transactions
        ),
        aggregated_data as (
            select report_date, category_id, sum(amount) as amount
            from transactions
            group by category_id, report_date
        )
    select category_id, report_date, amount
    from aggregated_data
    order by category_id, report_date, amount;
""".replace(
        "ifnull", sql.ifnull
    ).replace(
        "substr", sql.substr
    )
)

GET_ONE = text(
    """
    with
        recent_transactions as (
            select
                t.transaction_id,
                substring(cast(coalesce(t.clear_date, t.transaction_date) as varchar), 1, 7) as report_date,
                t.amount
            from quantum_transaction t
                inner join quantum_budget b
                    on b.category_id = t.category_id
                inner join quantum_account a
                    on a.account_id = t.account_id
                inner join quantum_portfolio p
                    on p.portfolio_id = a.portfolio_id
                inner join quantum_portfolio_user pu
                    on pu.portfolio_id = p.portfolio_id
            where
                b.budget_id = :budget_id and
                pu.user_id = :user_id and
                (clear_date is null or clear_date >= :limit_date)
        ),
        older_transactions as (
            select
                t.transaction_id,
                substring(cast(t.clear_date as varchar), 1, 7) as report_date,
                t.amount
            from quantum_transaction t
                inner join quantum_budget b
                    on b.category_id = t.category_id
                inner join quantum_account a
                    on a.account_id = t.account_id
                inner join quantum_portfolio p
                    on p.portfolio_id = a.portfolio_id
                inner join quantum_portfolio_user pu
                    on pu.portfolio_id = p.portfolio_id
                left join recent_transactions rt
                    on rt.transaction_id = t.transaction_id
            where
                b.budget_id = :budget_id and
                pu.user_id = :user_id and
                clear_date >= :limit_date and
                rt.transaction_id is null
        ),
        transactions as (
            select report_date, amount
            from older_transactions

            union all

            select report_date, amount
            from recent_transactions
        ),
        aggregated_data as (
            select report_date, sum(amount) as amount
            from transactions
            group by report_date
        )
    select report_date, amount
    from aggregated_data
    order by report_date, amount;
""".replace(
        "ifnull", sql.ifnull
    ).replace(
        "substr", sql.substr
    )
)
