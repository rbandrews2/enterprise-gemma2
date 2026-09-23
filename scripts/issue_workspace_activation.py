"""Operator-only activation issuance. Secret written exclusively to a named file."""
import argparse
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.workspace_preview.accounts import Accounts
from services.workspace_preview.postgres import PostgreSQLStorage


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--edition',choices=['core','enterprise'],required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    # Refuse accidental overwrite before generating a new entitlement.
    with args.output.open('x',encoding='utf-8') as file:
        storage=PostgreSQLStorage(os.environ['WZOS_DATABASE_URL'])
        accounts=Accounts(storage.connect,lambda token: None)
        file.write(accounts.issue_activation(args.edition))
    print('Activation saved to the requested file. Expires in seven days. No email was sent.')


if __name__=='__main__': main()
