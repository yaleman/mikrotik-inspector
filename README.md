# mikrotik-inspector

A Python CLI tool for connecting to MikroTik routers via SSH and running commands to retrieve structured data.

## What It Does

mikrotik-inspector connects to MikroTik routers over SSH and executes commands, parsing the output into JSON format. It's particularly useful for extracting DHCP lease information and other structured data from MikroTik devices.

## Usage

Basic command:

```bash
mikrotik-inspector --host router.example.com "/ip dhcp-server lease print detail"
```

With custom username:

```bash
mikrotik-inspector --host router.example.com --user admin "/ip dhcp-server lease print detail"
```

Enable debug logging:

```bash
mikrotik-inspector --host router.example.com --debug "/ip dhcp-server lease print detail"
```

## Configuration

You can set default values using environment variables:

- `MIKROTIK_HOSTNAME`: Default router hostname
- `MIKROTIK_USER`: SSH username (defaults to your current user)

Example:

```bash
export MIKROTIK_HOSTNAME=router.example.com
export MIKROTIK_USER=admin
mikrotik-inspector "/ip dhcp-server lease print detail"
```

## Output

The tool outputs JSON objects, one per line, with parsed data from the MikroTik command output. Use standard Unix tools to process the output:

```bash
# Pretty-print JSON
mikrotik-inspector --host router.example.com "/ip dhcp-server lease print detail" | jq

# Filter specific fields
mikrotik-inspector --host router.example.com "/ip dhcp-server lease print detail" | jq '.["mac-address"]'
```

## Authentication

The tool uses SSH key-based authentication through Fabric/Paramiko. Ensure your SSH keys are properly configured for the target MikroTik device.
