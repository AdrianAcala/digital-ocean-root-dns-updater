#!/usr/bin/env python3
"""Application that updates A records for domains on DigitalOcean to your local IP address."""
import digitalocean
import requests
import sqlite3
import os

global db_location

def create_sqlite_db():
    """Create an SQLite database to store the last IP address."""
    global db_location
    # Create database if it doesn't exist
    if not os.path.isfile(db_location):
        conn = sqlite3.connect("last_ip.db")
        c = conn.cursor()
        c.execute("CREATE TABLE last_ip (ip text)")
        conn.commit()
        conn.close()


def get_last_ip():
    """Gets the last IP address from the database. If it doesn't exist, return None."""
    global db_location
    conn = sqlite3.connect(db_location)
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


def clear_last_ip_table():
    """Clear the last IP address table."""
    global db_location
    conn = sqlite3.connect(db_location)
    c = conn.cursor()
    c.execute("DELETE FROM last_ip")
    conn.commit()
    conn.close()


def update_last_ip_in_db(ip):
    """Update the last IP address in the database."""
    global db_location
    conn = sqlite3.connect(db_location)
    c = conn.cursor()
    c.execute("INSERT INTO last_ip VALUES (?)", (ip,))
    conn.commit()
    conn.close()


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

        clear_last_ip_table()
        update_last_ip_in_db(my_ip)


def main():
    """Main method"""
    # Grab the environment variable `do_dns_domains` and split it into a list
    _domains = os.environ.get("do_dns_domains")
    if _domains is None:
        print("Environment variable `do_dns_domains` not set. Exiting.")
        return
    else:
        # Split the string of domains into a list of domains
        domains = []
        for domain in _domains.split(","):
            domain = domain.strip()
            if not domain:
                continue
            domains.append(domain)

    global db_location
    db_location = "/tmp/do_dns_updater.cache"

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
