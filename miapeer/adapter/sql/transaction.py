from sqlmodel import text

GET_ALL = text(
    """
    with
        account as (
            select account_id, starting_balance
            from quantum_account
            where account_id = :account_id
        ),
        recent_transactions as (
            select
                t.account_id,
                t.transaction_id,
                t.transaction_date,
                t.clear_date,
                t.transaction_type_id,
                t.check_number,
                t.payee_id,
                t.category_id,
                t.amount,
                t.notes,
                t.exclude_from_forecast
            from quantum_transaction t
                inner join quantum_account a
                    on a.account_id = t.account_id
                inner join quantum_portfolio p
                    on p.portfolio_id = a.portfolio_id
                inner join quantum_portfolio_user pu
                    on pu.portfolio_id = p.portfolio_id
            where
               a.account_id = :account_id and
               pu.user_id = :user_id and
               clear_date is null or clear_date >= :limit_date
        ),
        older_transactions_sum as (
            select min(t.account_id) as account_id, sum(t.amount) as sum_of_old
            from quantum_transaction t
                inner join quantum_account a
                    on a.account_id = t.account_id
                inner join quantum_portfolio p
                    on p.portfolio_id = a.portfolio_id
                inner join quantum_portfolio_user pu
                    on pu.portfolio_id = p.portfolio_id
                left join recent_transactions rt
                    on rt.transaction_id = t.transaction_id
            where
                a.account_id = :account_id and
                pu.user_id = :user_id and
                rt.transaction_id is null
        ),
        ordered_transactions as (
            select
                account_id,
                null as transaction_id,
                null as transaction_date,
                null as clear_date,
                null as transaction_type_id,
                null as check_number,
                null as payee_id,
                null as category_id,
                starting_balance as amount,
                null as notes,
                null as exclude_from_forecast,
                -2 as order_index
            from account

            union all

            select
                account_id,
                null as transaction_id,
                null as transaction_date,
                null as clear_date,
                null as transaction_type_id,
                null as check_number,
                null as payee_id,
                null as category_id,
                sum_of_old as amount,
                null as notes,
                null as exclude_from_forecast,
                -1 as order_index
            from older_transactions_sum

            union all

            select
                account_id,
                transaction_id,
                transaction_date,
                clear_date,
                transaction_type_id,
                check_number,
                payee_id,
                category_id,
                amount,
                notes,
                exclude_from_forecast,
                row_number() over (ORDER BY ifnull(clear_date, '9999-01-01'), transaction_date) as order_index
            from recent_transactions
        )
    select
        account_id,
        transaction_id,
        transaction_date,
        clear_date,
        transaction_type_id,
        check_number,
        payee_id,
        category_id,
        amount,
        notes,
        exclude_from_forecast,
        order_index,
        SUM(amount) OVER (ORDER BY order_index) AS balance
    from ordered_transactions
    order by order_index;
"""
)
