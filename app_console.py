"""
Console mini-app to create OPC UA certificates.

Menu:
1) Create CA
2) Create server certificate
3) Create client certificate
4) Edit default configuration
5) Exit
"""

from src.ca import create_ca
from src.server_cert import create_server_certificate
from src.client_cert import create_client_certificate
from src.config import load_config, save_config, DEFAULT_CONFIG


def ask_text(prompt: str, default: str | None = None, required: bool = False) -> str:
    """
    Ask the user for a text input.

    - If required=True, does not accept empty.
    - If there is a default and user leaves it empty, use the default.
    """
    while True:
        if default:
            value = input(f"{prompt} [{default}]: ").strip()
        else:
            value = input(f"{prompt}: ").strip()

        if not value:
            if required and not default:
                print("This field is required. Please enter a value.")
                continue
            if required and default:
                # If required but there is a default, use default if left empty
                return default
            if not required:
                return value if value else (default or "")
        return value if value else (default or "")


def ask_int(prompt: str, default: int, minimum: int | None = None, maximum: int | None = None) -> int:
    """
    Ask the user for an integer input with optional range validation.
    """
    while True:
        value = input(f"{prompt} [{default}]: ").strip()
        if not value:
            return default
        try:
            num = int(value)
        except ValueError:
            print("Must be an integer.")
            continue

        if minimum is not None and num < minimum:
            print(f"Minimum value is {minimum}.")
            continue
        if maximum is not None and num > maximum:
            print(f"Maximum value is {maximum}.")
            continue

        return num


def ask_text_list(prompt: str) -> list[str] | None:
    """
    Ask the user for a comma-separated list of texts.
    Returns None if the user leaves the line empty.
    """
    value = input(f"{prompt} (comma-separated, or leave empty): ").strip()
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def ask_key_size(entity: str) -> int:
    """
    Ask the user for the key size for a given entity (CA, server, client).
    Options: 2048 or 4096.
    """
    print(f"Key size for {entity} (2048 or 4096):")
    while True:
        value = input("Enter 2048 or 4096 [2048]: ").strip()
        if not value:
            return 2048
        if value not in ("2048", "4096"):
            print("Invalid option. Enter 2048 or 4096.")
            continue
        return int(value)


def create_ca_option(config: dict) -> None:
    """
    Ask parameters to create a CA and create it.
    """
    print("\n=== Create CA ===")

    country = ask_text("Country", config["country"])
    state = ask_text("State / Province", config["state"])
    locality = ask_text("Locality", config["locality"])
    org = ask_text("Organization", config["organization"])
    common_name = ask_text(
        "Common Name (CN)",
        config["common_name_ca"],
        required=True,
    )

    validity_days = ask_int(
        "Validity (days)",
        config["validity_days_ca"],
        minimum=1,
    )

    key_size = ask_key_size("CA")

    print("\nCreating CA...")

    try:
        create_ca(
            ca_folder="certs/ca",
            key_size=key_size,
            country_name=country,
            state_name=state,
            locality_name=locality,
            organization_name=org,
            common_name=cn,
            validity_days=validity,
        ) 
        print("CA created successfully.")
        print("Files generated in: certs/ca/")
        print("  - ca_key.pem  (private key)")
        print("  - ca_cert.pem (certificate)")
    except Exception as e:
        print(f"Error creating CA: {e}")


def create_server_option(config: dict) -> None:
    """
    Ask parameters to create a server certificate and create it.
    """
    print("\n=== Create server certificate ===")

    country = ask_text("Country", config["country"])
    state = ask_text("State / Province", config["state"])
    locality = ask_text("Locality", config["locality"])
    org = ask_text("Organization", config["organization"])
    common_name = ask_text(
        "Common Name (CN) / hostname",
        config["common_name_server"],
        required=True,
    )

    print(
        "Subject Alternative Names (SAN). Example:\n"
        "  DNS:servidor-opcua.local,DNS:localhost,IP:127.0.0.1\n"
        "You can leave it empty if you don't want SAN."
    )
    san_input = ask_text_list("SAN")

    validity_days = ask_int(
        "Validity (days)",
        config["validity_days_server"],
        minimum=1,
    )

    key_size = ask_key_size("server")

    print("\nCreating server certificate...")

    try:
        create_server_certificate(
            server_folder="certs/server",
            ca_folder="certs/ca",
            key_size=key_size,
            country_name=country,
            state_name=state,
            locality_name=locality,
            organization_name=org,
            common_name=common_name,
            san_list=san_input,
            validity_days=validity_days,
        )
        print("Server certificate created successfully.")
        print("Files generated in: certs/server/")
        print("  - server_key.pem  (private key)")
        print("  - server_cert.pem (certificate)")
    except Exception as e:
        print(f"Error creating server certificate: {e}")


def create_client_option(config: dict) -> None:
    """
    Ask parameters to create a client certificate and create it.
    """
    print("\n=== Create client certificate ===")

    country = ask_text("Country", config["country"])
    state = ask_text("State / Province", config["state"])
    locality = ask_text("Locality", config["locality"])
    org = ask_text("Organization", config["organization"])
    common_name = ask_text(
        "Common Name (CN) / client identifier",
        config["common_name_client"],
        required=True,
    )

    print(
        "Subject Alternative Names (SAN). Example:\n"
        "  DNS:client1.local,IP:192.168.1.20\n"
        "You can leave it empty if you don't want SAN."
    )
    san_input = ask_text_list("SAN")

    validity_days = ask_int(
        "Validity (days)",
        config["validity_days_client"],
        minimum=1,
    )

    key_size = ask_key_size("client")

    print("\nCreating client certificate...")

    try:
        create_client_certificate(
            client_folder="certs/client",
            ca_folder="certs/ca",
            key_size=key_size,
            country_name=country,
            state_name=state,
            locality_name=locality,
            organization_name=org,
            common_name=common_name,
            san_list=san_input,
            validity_days=validity_days,
        )
        print("Client certificate created successfully.")
        print("Files generated in: certs/client/")
        print("  - client_key.pem  (private key)")
        print("  - client_cert.pem (certificate)")
    except Exception as e:
        print(f"Error creating client certificate: {e}")


def edit_config_option() -> None:
    """
    Allow editing the default configuration (config.json).
    """
    print("\n=== Edit default configuration ===")

    config = load_config()

    print("Enter new default values (leave empty to keep current).")

    config["country"] = ask_text("Country", config["country"])
    config["state"] = ask_text("State / Province", config["state"])
    config["locality"] = ask_text("Locality", config["locality"])
    config["organization"] = ask_text("Organization", config["organization"])
    config["common_name_ca"] = ask_text("Common Name (CN) for CA", config["common_name_ca"])
    config["common_name_server"] = ask_text("Common Name (CN) for server", config["common_name_server"])
    config["common_name_client"] = ask_text("Common Name (CN) for client", config["common_name_client"])

    config["validity_days_ca"] = ask_int("Validity (CA, days)", config["validity_days_ca"], minimum=1)
    config["validity_days_server"] = ask_int("Validity (server, days)", config["validity_days_server"], minimum=1)
    config["validity_days_client"] = ask_int("Validity (client, days)", config["validity_days_client"], minimum=1)

    try:
        save_config(config)
        print("Configuration saved to config.json")
    except Exception as e:
        print(f"Error saving configuration: {e}")


def show_menu() -> None:
    """
    Show the main menu and handle the chosen option.
    """
    config = load_config()

    while True:
        print("\n=== OPC UA Certificate Generator ===")
        print("1) Create CA")
        print("2) Create server certificate")
        print("3) Create client certificate")
        print("4) Edit default configuration")
        print("5) Exit")

        option = input("\nChoose an option (1-5): ").strip()

        if option == "1":
            create_ca_option(config)
        elif option == "2":
            create_server_option(config)
        elif option == "3":
            create_client_option(config)
        elif option == "4":
            edit_config_option()
            # Reload config in case it changed
            config = load_config()
        elif option == "5":
            print("Exiting...")
            break
        else:
            print("Invalid option. Enter 1, 2, 3, 4 or 5.")


if __name__ == "__main__":
    show_menu()