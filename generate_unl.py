import os
import yaml
import ipaddress
import xml.etree.ElementTree as ET
from xml.dom import minidom
import uuid

def load_template(template_name):
    """Load template configuration from YAML file."""
    template_path = f"./templates/{template_name}.yml"
    with open(template_path, 'r') as file:
        return yaml.safe_load(file)

def get_router_info():
    """Get router information from user including a prefix for router names"""
    router_prefix = input("Enter the router name prefix: ")
    while True:
        try:
            router_count = int(input("Enter the number of routers: "))
            if router_count <= 0:
                print("Please enter a positive number.")
            else:
                break
        except ValueError:
            print("Invalid input. Please enter a number.")
    return [f"{router_prefix}{i+1}" for i in range(router_count)]

def get_connections(routers):
    """Get connections between routers from user"""
    connections = []
    for i in range(len(routers)):
        for j in range(i+1, len(routers)):
            connection = input(f"Is {routers[i]} connected to {routers[j]}? (y/n): ")
            if connection.lower() == 'y':
                connections.append((routers[i], routers[j]))
    return connections

def get_prefix():
    """Get prefix from user"""
    while True:
        try:
            prefix = input("Enter prefix (e.g., 10.0.0.0/16): ")
            return ipaddress.ip_network(prefix, strict=False)
        except ValueError:
            print("Invalid IP network. Please try again.")

def get_lab_name():
    """Get lab name from user"""
    return input("Enter lab name: ")

def get_eve_ng_template():
    """Get EVE-NG template from user"""
    return input("Enter EVE-NG template (e.g., iol): ")

def get_eve_ng_image():
    """Get EVE-NG image from user"""
    return input("Enter EVE-NG image (e.g., x86_64_crb_linux-adventerprisek9-ms.bin): ")

def generate_subnets(prefix, connections, routers):
    """Generate subnets for each connection"""
    subnets = {}
    subnet_generator = prefix.subnets(new_prefix=24)
    for connection in connections:
        subnet = next(subnet_generator)
        router1_index = routers.index(connection[0]) + 1
        router2_index = routers.index(connection[1]) + 1
        label = f"{subnet.network_address}.{router1_index}{router2_index}.0/24"
        subnets[connection] = label
    return subnets

def generate_unl_file(lab_name, routers, connections, subnets, template_name, image):
    """Generate .unl file with correct interface naming for iol template and networks for connections"""
    template = load_template(template_name)
    unl_file = f"{lab_name}.unl"
    lab = ET.Element("lab")
    lab.set("name", lab_name)
    lab.set("id", str(uuid.uuid4()))
    lab.set("version", "1")
    lab.set("scripttimeout", "300")
    lab.set("countdown", "0")
    lab.set("linkwidth", "2")
    lab.set("lock", "0")
    lab.set("grid", "1")
    lab.set("sat", "-1")

    topology = ET.SubElement(lab, "topology")

    nodes = ET.SubElement(topology, "nodes")
    node_id = 1
    network_id = 1
    x = 100
    y = 100
    router_interfaces = {}
    router_connections = {router: sum(1 for conn in connections if router in conn) for router in routers}

    for router in routers:
        node = ET.SubElement(nodes, "node")
        node.set("id", str(node_id))
        node.set("name", router)
        node.set("type", template['type'])
        node.set("template", template_name)
        node.set("image", image)
        node.set("nvram", str(template['nvram']))
        node.set("ram", str(template['ram']))
        node.set("serial", str(template['serial']))
        node.set("keepalive", str(template['keepalive']))
        node.set("sat", "-1")
        node.set("icon", template['icon'])
        node.set("config", "0")
        node.set("left", str(x))
        node.set("top", str(y))
        if template_name == 'iol':
            ethernet_count = (router_connections[router] + 3) // 4  # Ceiling division to determine ethernet slots required
            node.set("ethernet", str(ethernet_count))  # Set the ethernet attribute based on the number of interfaces
        else:
            node.set("ethernet", str(template['ethernet']))

        router_interfaces[router] = []
        slot = 0
        port = 0

        for i in range(router_connections[router]):  # Create interfaces based on connections
            if template_name == 'iol':
                slot = i // 4
                interface_name = f"e{slot}/{port}"
                base_id = slot  # Base ID for the slot
                interface_id = base_id + (port * 16)  # ID calculation based on slot and port
            else:
                interface_name = f"gi0/{i}"
                interface_id = i  # Use a simple incremental id for non-IOL templates

            interface = ET.SubElement(node, "interface")
            interface.set("id", str(interface_id))
            interface.set("name", interface_name)
            interface.set("type", "ethernet")
            interface.set("vid", "1")
            interface.set("labelpos", "0.5")
            interface.set("stub", "0")
            interface.set("width", "2")
            interface.set("curviness", "10")
            interface.set("beziercurviness", "150")
            interface.set("round", "0")
            interface.set("midpoint", "0.5")
            interface.set("srcpos", "0.15")
            interface.set("dstpos", "0.85")
            router_interfaces[router].append(interface)
            
            port += 1
            if port == 4:
                port = 0
                slot += 1

        node_id += 1
        x += 200
        if node_id % 4 == 0:
            x = 100
            y += 200

    networks = ET.SubElement(topology, "networks")
    for connection in connections:
        network = ET.SubElement(networks, "network")
        network.set("id", str(network_id))
        network.set("smart", "0")
        network.set("vlan8021ad", "0")
        network.set("type", "bridge")
        network.set("name", f"Net-{connection[0]}-{connection[1]}")
        network.set("left", "1041")
        network.set("top", "406")
        network.set("style", "Solid")
        network.set("linkstyle", "Straight")
        network.set("color", "")
        network.set("label", subnets[connection])
        network.set("visibility", "0")
        network.set("icon", "lan.png")

        router1_interface = None
        router2_interface = None
        for interface in router_interfaces[connection[0]]:
            if interface.get("network_id") is None or interface.get("network_id") == "":
                router1_interface = interface
                break
        for interface in router_interfaces[connection[1]]:
            if interface.get("network_id") is None or interface.get("network_id") == "":
                router2_interface = interface
                break

        if router1_interface is not None and router2_interface is not None:
            print(f"Setting network_id {network_id} for connection between {connection[0]} and {connection[1]}")
            
            # Update the XML to ensure network_id is properly added under the interface node
            router1_interface.set("network_id", str(network_id))
            router1_interface.set("color", "#3e7089")
            router1_interface.set("style", "Solid")
            router1_interface.set("linkstyle", "Straight")
            router1_interface.set("label", subnets[connection])
            
            router2_interface.set("network_id", str(network_id))
            router2_interface.set("color", "#3e7089")
            router2_interface.set("style", "Solid")
            router2_interface.set("linkstyle", "Straight")
            router2_interface.set("label", subnets[connection])

        else:
            print(f"Warning: Could not find interfaces for connection {connection}")

        network_id += 1

    tree = ET.ElementTree(lab)
    xmlstr = minidom.parseString(ET.tostring(tree.getroot())).toprettyxml(indent="   ")
    with open(unl_file, "w") as f:
        f.write(xmlstr)

    print(f".unl file generated: {unl_file}")
    print("Interfaces for each router:")
    for router, interfaces in router_interfaces.items():
        print(f"{router}: {[interface.get('name') for interface in interfaces]}")

    # Generate YAML output
    yaml_data = {"nodes": {}}
    for router in routers:
        yaml_data["nodes"][router] = {}
        for interface in router_interfaces[router]:
            # Ensure label is set before adding to YAML
            if interface.get("label"):
                yaml_data["nodes"][router][interface.get("name")] = interface.get("label")
            else:
                yaml_data["nodes"][router][interface.get("name")] = "No Label"

    with open(f"{lab_name}.yaml", "w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False)

    print(f"YAML file generated: {lab_name}.yaml")

def main():
    lab_name = get_lab_name()
    routers = get_router_info()
    connections = get_connections(routers)
    prefix = get_prefix()
    template_name = get_eve_ng_template()
    image = get_eve_ng_image()
    subnets = generate_subnets(prefix, connections, routers)
    generate_unl_file(lab_name, routers, connections, subnets, template_name, image)

if __name__ == "__main__":
    main()