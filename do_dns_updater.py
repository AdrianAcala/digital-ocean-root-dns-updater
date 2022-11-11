#!/usr/bin/env python3
"""Application that updates A records for domains on DigitalOcean to your local IP address."""
import digitalocean
import requests
import sqlite3
import os


def create_sqlite_db():
    """Create an SQLite database to store the last IP address."""
    
    conn = sqlite3.connect("last_ip.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS last_ip (ip)""")
    conn.commit()
    conn.close()


def get_last_ip():
    """Gets the last IP address from the database. If it doesn't exist, return None."""
    conn = sqlite3.connect("last_ip.db")
    c = conn.cursor()
    c.execute("SELECT ip FROM last_ip")
    last_ip = c.fetchone()
    conn.close()
    if last_ip is None:
        return None
    return last_ip[0]


def get_my_ip():
    """Get the current IP address of the machine."""
    return requests.get("https://api.ipify.org", timeout=5).text


def update_last_ip(my_ip, token, domains):
    """Update the IP address on DigitalOcean"""
    for domain in domains:
        # Get a list of all the current domain records
        domain = digitalocean.Domain(token=token, name=domain)
        records = domain.get_records()

        # Update the record
        for record in records:
            if record.type == "A" and record.name == "@":
                if record.data != my_ip:
                    record.data = my_ip
                    record.save()

        # Clear last_ip table
        conn = sqlite3.connect("last_ip.db")
        c = conn.cursor()
        c.execute("DELETE FROM last_ip")
        conn.commit()

        # Save IP address to database
        c = conn.cursor()
        c.execute("INSERT INTO last_ip VALUES (?)", (my_ip,))
        conn.commit()
        conn.close()


def main():
    """Main method"""
    # Grab the environment variable `do_dns_domains` and split it into a list
    _domains = os.environ.get("do_dns_domains")
    if _domains is None:
        print("Environment variable `do_dns_domains` not set. Exiting.")
        return
    else:
        domains = _domains.split(",")

    # Grab the environment variable `do_dns_token`
    token = os.environ.get("do_dns_token")
    if token is None:
        print("Environment variable `do_dns_token` not set. Exiting.")
        return

    # Creates database if it doesn't exist
    create_sqlite_db()

    # Get the last external IP address from the database
    last_ip = get_last_ip()

    # Get the current external IP address
    my_ip = get_my_ip()

    # If the IP address in the database is empty
    # Or if the current IP address is different from the last IP address
    # Then update the IP address on DigitalOcean
    if last_ip is None or last_ip != my_ip:
        update_last_ip(get_my_ip(), token, domains)


if __name__ == "__main__":
    main()
