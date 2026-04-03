import csv
from datetime import datetime

def main():
    valid_rows = []
    rejected_rows = []
    seen_transaction_ids = set()
    rejection_counts = {
        "TransactionID missing or not unique": 0,
        "Invalid Date format or value": 0,
        "Amount not positive": 0,
        "Invalid Currency": 0
    }
    processed_rows = 0
    
    with open('transactions.csv', mode='r', newline='') as infile:
        reader = csv.DictReader(infile)
        header = reader.fieldnames
        
        for row in reader:
            processed_rows += 1
            errors = []
            
            # Rule 1: TransactionID Uniqueness & Format
            transaction_id = row.get('TransactionID')
            if not transaction_id or transaction_id in seen_transaction_ids:
                errors.append("TransactionID missing or not unique")
            
            # Add to seen_ids for subsequent checks, even if other errors exist
            if transaction_id:
                seen_transaction_ids.add(transaction_id)

            # Rule 2: Date Format & Validity
            date_str = row.get('Date')
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
            except (ValueError, TypeError):
                errors.append("Invalid Date format or value")

            # Rule 3: Amount Value
            amount_str = row.get('Amount')
            try:
                amount = float(amount_str)
                if amount <= 0:
                    errors.append("Amount not positive")
            except (ValueError, TypeError):
                errors.append("Amount not positive")
            
            # Rule 4: Currency Code
            currency = row.get('Currency')
            if currency not in ['USD', 'EUR', 'GBP']:
                errors.append("Invalid Currency")

            if errors:
                # Convert ordered dict to list to append error
                row_list = list(row.values())
                row_list.append(','.join(sorted(list(set(errors))))) # sort for consistent error order
                rejected_rows.append(row_list)
                for error in set(errors):
                    if error in rejection_counts:
                        rejection_counts[error] += 1
            else:
                valid_rows.append(row)

    # Write valid transactions to output.csv
    with open('output.csv', mode='w', newline='') as outfile:
        if valid_rows:
            writer = csv.DictWriter(outfile, fieldnames=header)
            writer.writeheader()
            writer.writerows(valid_rows)
        else: # Create empty file with header if no valid rows
            writer = csv.writer(outfile)
            writer.writerow(header)


    # Write rejected transactions to rejected.csv
    with open('rejected.csv', mode='w', newline='') as rejected_file:
        writer = csv.writer(rejected_file)
        extended_header = header + ['Error']
        writer.writerow(extended_header)
        writer.writerows(rejected_rows)

    # Print summary to console
    print(f"Processed: {processed_rows} rows")
    print(f"Accepted: {len(valid_rows)} rows")
    print(f"Rejected: {len(rejected_rows)} rows")
    print("\nRejection Reasons:")
    for reason, count in rejection_counts.items():
        print(f"- {reason}: {count} times")

if __name__ == "__main__":
    main()
