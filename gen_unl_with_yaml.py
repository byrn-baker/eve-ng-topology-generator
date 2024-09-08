import yaml
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import uuid
import os
import ipaddress
import math

def load_template(template_type):
    template_file = os.path.join('templates', f"{template_type}.yml")
    if os.path.exists(template_file):
        with open(template_file, 'r') as file:
            return yaml.safe_load(file)
    else:
        print(f"Warning: Template file for {template_type} not found.")
        return {}

def create_unl(yaml_data, lab_name):
    # Root element with dynamic UUID
    lab_uuid = str(uuid.uuid4())
    lab = Element('lab', attrib={
        'name': lab_name,
        'id': lab_uuid,
        'version': '1',
        'scripttimeout': '300',
        'countdown': '0',
        'linkwidth': '2',
        'lock': '0',
        'grid': '1',
        'sat': '-1'
    })

    topology = SubElement(lab, 'topology')
    nodes = SubElement(topology, 'nodes')
    networks = SubElement(topology, 'networks')

    # Network ID mappings
    network_mappings = {}
    interface_counter_map = {}
    connections = []

    # Gather connections
    for router in yaml_data['routers']:
        for interface in router['interfaces']:
            connect_to = interface.get('connect_to')
            if connect_to:
                connection_key = tuple(sorted([router['name'], connect_to]))
                connections.append(connection_key)

    # Map connections to unique network IDs
    for i, connection in enumerate(set(connections)):
        network_key = []
        for router in yaml_data['routers']:
            for interface in router['interfaces']:
                connect_to = interface.get('connect_to')
                if connect_to and tuple(sorted([router['name'], connect_to])) == connection:
                    ipv4 = interface.get('ipv4', '')
                    ipv6 = interface.get('ipv6', '')
                    if ipv4:
                        ipv4_network = ipaddress.IPv4Network(ipv4, strict=False)
                        network_key.append(f"{ipv4_network}")
                    if ipv6:
                        ipv6_network = ipaddress.IPv6Network(ipv6, strict=False)
                        network_key.append(f"{ipv6_network}")
        network_key = tuple(sorted(network_key))
        network_mappings[connection] = network_key

    # Create a mapping of network keys to unique IDs
    network_id_mappings = {}
    for i, network_key in enumerate(set(network_mappings.values())):
        network_id_mappings[network_key] = i + 1

    # Update the network IDs in the network mappings
    for connection, network_key in network_mappings.items():
        network_mappings[connection] = network_id_mappings[network_key]

    # Calculate the number of rows and columns for the grid
    num_routers = len(yaml_data['routers'])
    num_cols = math.ceil(math.sqrt(num_routers))
    num_rows = math.ceil(num_routers / num_cols)

    # Create nodes
    for i, router in enumerate(yaml_data['routers']):
        template_data = load_template(router['type'])
        template_type = router['type'].lower()
        
        # Initialize interface ID counter based on template type
        if template_type == 'xrv9k':
            interface_counter = 3
        else:
            interface_counter = 0

        # Add 3 to the total number of interfaces for xrv9k template
        if template_type == 'xrv9k':
            ethernet = str(len(router['interfaces']) + 3)
        elif template_type == 'iol':
            ethernet = str(len(router['interfaces']) + 3) // 4 
        else:
            ethernet = str(len(router['interfaces']))

        # Calculate the position of the node
        col = i % num_cols
        row = i // num_cols
        left = 100 + col * 200
        top = 100 + row * 200

        node = SubElement(nodes, 'node', attrib={
            'id': str(len(nodes) + 1),
            'name': router['name'],
            'type': template_data.get('type', 'qemu'),
            'template': template_type,
            'image': router['image'].lower(),
            'console': template_data.get('console', 'telnet'),
            'cpu': str(template_data.get('cpu', 4)),
            'cpulimit': str(template_data.get('cpulimit', 0)),
            'ram': str(template_data.get('ram', 16384)),
            'ethernet': ethernet,
            'uuid': str(uuid.uuid4()),
            'firstmac': '50:00:00:01:00:00',
            'qemu_options': template_data.get('qemu_options', ''),
            'qemu_version': template_data.get('qemu_version', '5.2.0'),
            'qemu_arch': template_data.get('qemu_arch', 'x86_64'),
            'qemu_nic': template_data.get('qemu_nic', 'e1000'),
            'delay': str(template_data.get('delay', 0)),
            'sat': '-1',
            'icon': template_data.get('icon', 'Router-2D-Gen-White-S.svg'),
            'config': '0',
            'left': str(left),
            'top': str(top)
        })

        for interface in router['interfaces']:
            connect_to = interface.get('connect_to')
            if connect_to:
                connection_key = tuple(sorted([router['name'], connect_to]))
                network_id = network_mappings.get(connection_key, None)

                if network_id is not None:
                    interface_elem = SubElement(node, 'interface', attrib={
                        'id': str(interface_counter),
                        'name': interface['name'],
                        'type': 'ethernet',
                        'network_id': str(network_id),
                        'vid': '1',
                        'labelpos': '0.5',
                        'stub': '0',
                        'width': '2',
                        'curviness': '10',
                        'beziercurviness': '150',
                        'round': '0',
                        'midpoint': '0.5',
                        'srcpos': '0.15',
                        'dstpos': '0.85'
                    })

                    # Increment interface ID based on template type
                    if template_type == 'iol':
                        interface_counter += 16
                    else:
                        interface_counter += 1

    # Create networks based on the mappings
    for connection, network_id in network_mappings.items():
        network_name = f"Net-{'-'.join(connection)}"
        network_label = ''
        ipv4_set = set()
        ipv6_set = set()
        for router in yaml_data['routers']:
            for interface in router['interfaces']:
                connect_to = interface.get('connect_to')
                if connect_to and tuple(sorted([router['name'], connect_to])) == connection:
                    ipv4 = interface.get('ipv4', '')
                    ipv6 = interface.get('ipv6', '')
                    if ipv4:
                        ipv4_network = ipaddress.IPv4Network(ipv4, strict=False)
                        ipv4_set.add(f"{ipv4_network.network_address}/{ipv4_network.prefixlen}")
                    if ipv6:
                        ipv6_network = ipaddress.IPv6Network(ipv6, strict=False)
                        ipv6_set.add(f"{ipv6_network.network_address}/{ipv6_network.prefixlen}")

        # Build the label from unique networks
        network_label = " - ".join(ipv4_set.union(ipv6_set))

        network = SubElement(networks, 'network', attrib={
            'id': str(network_id),
            'smart': '0',
            'vlan8021ad': '0',
            'type': 'bridge',
            'name': network_name,
            'left': '50',
            'top': str(50 + network_id * 50),
            'style': 'Solid',
            'linkstyle': 'Straight',
            'visibility': '0',
            'icon': 'lan.png',
            'label': network_label.strip()
        })

    # Convert to string and pretty-print
    rough_string = tostring(lab, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")

    # Remove extra XML declaration line if it exists
    if pretty_xml.startswith('<?xml version="1.0" ?>\n'):
        pretty_xml = pretty_xml.replace('<?xml version="1.0" ?>\n', '', 1)

    return pretty_xml

# Ask for lab name and YAML file name
lab_name = input("Enter the name for the lab: ")
yaml_file_name = input("Enter the name of the YAML file (including .yaml): ")

# Load YAML data
with open(yaml_file_name, 'r') as file:
    yaml_data = yaml.safe_load(file)

# Generate UNL
unl_content = create_unl(yaml_data, lab_name)

# Write to file
output_file_name = f"{lab_name}.unl"
with open(output_file_name, 'w') as file:
    file.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
    file.write(unl_content)

print(f"UNL file '{output_file_name}' has been generated with a unique UUID and network labels.")