import os
import ipaddress
import xml.etree.ElementTree as ET
from xml.dom import minidom
import uuid
import yaml

def get_router_info():
    """Get router information from user"""
    router_count = int(input("Enter the number of routers: "))
    routers = []
    for i in range(router_count):
        router_name = input(f"Enter router {i+1} name: ")
        routers.append(router_name)
    return routers

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
    prefix = input("Enter prefix (e.g., 10.0.0.0/16): ")
    return ipaddress.ip_network(prefix, strict=False)

def get_lab_name():
    """Get lab name from user"""
    lab_name = input("Enter lab name: ")
    return lab_name

def get_eve_ng_template():
    """Get EVE-NG template from user"""
    template = input("Enter EVE-NG template (e.g., iol): ")
    return template

def get_eve_ng_image():
    """Get EVE-NG image from user"""
    image = input("Enter EVE-NG image (e.g., x86_64_crb_linux-adventerprisek9-ms.bin): ")
    return image

def generate_subnets(prefix, connections, routers):
    """Generate subnets for each connection"""
    subnets = {}
    subnet_generator = prefix.subnets(new_prefix=24)  # Generate /24 subnets
    for connection in connections:
        subnet = next(subnet_generator)
        router1_index = routers.index(connection[0]) + 1
        router2_index = routers.index(connection[1]) + 1
        label = f"{subnet.network_address}.{router1_index}{router2_index}.0/24"
        subnets[connection] = label
    return subnets

def generate_unl_file(lab_name, routers, connections, subnets, template, image):
    """Generate .unl file"""
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
    interface_id = 0
    network_id = 1
    x = 100
    y = 100
    router_interfaces = {}
    for router in routers:
        node = ET.SubElement(nodes, "node")
        node.set("id", str(node_id))
        node.set("name", router)
        node.set("type", template)
        node.set("template", template)
        node.set("image", image)
        node.set("ethernet", "4")
        node.set("nvram", "1024")
        node.set("ram", "1024")
        node.set("serial", "0")
        node.set("keepalive", "0")
        node.set("delay", "0")
        node.set("sat", "-1")
        node.set("icon", "Router-2D-Gen-White-S.svg")
        node.set("config", "0")
        node.set("left", str(x))
        node.set("top", str(y))

        router_interfaces[router] = []
        for i in range(4):
            interface = ET.SubElement(node, "interface")
            interface.set("id", str(i))
            interface.set("name", f"e0/{i}")
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

        node_id += 1
        x += 200
        if node_id % 4 == 0:
            x = 100
            y += 200

    networks = ET.SubElement(topology, "networks")
    network_id = 1
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
        network.set("label", "")
        network.set("visibility", "0")
        network.set("icon", "lan.png")

        router1_interface = None
        router2_interface = None
        for interface in router_interfaces[connection[0]]:
            if interface.get("network_id") is None:
                router1_interface = interface
                break
        for interface in router_interfaces[connection[1]]:
            if interface.get("network_id") is None:
                router2_interface = interface
                break

        for node in nodes.findall("node"):
            if node.get("name") == connection[0]:
                for interface in node.findall("interface"):
                    if interface == router1_interface:
                        interface.set("network_id", str(network_id))
                        interface.set("color", "#3e7089")
                        interface.set("style", "Solid")
                        interface.set("linkstyle", "Straight")
                        interface.set("label", subnets[connection])
            if node.get("name") == connection[1]:
                for interface in node.findall("interface"):
                    if interface == router2_interface:
                        interface.set("network_id", str(network_id))
                        interface.set("color", "#3e7089")
                        interface.set("style", "Solid")
                        interface.set("linkstyle", "Straight")
                        interface.set("label", subnets[connection])

        network_id += 1

    tree = ET.ElementTree(lab)
    xmlstr = minidom.parseString(ET.tostring(tree.getroot())).toprettyxml(indent="   ")
    with open(unl_file, "w") as f:
        f.write(xmlstr)

    print(f".unl file generated: {unl_file}")

    # Generate YAML output
    yaml_data = {"nodes": {}}
    for router in routers:
        yaml_data["nodes"][router] = {}
        for interface in router_interfaces[router]:
            yaml_data["nodes"][router][interface.get("name")] = interface.get("label")

    with open(f"{lab_name}.yaml", "w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False)

    print(f"YAML file generated: {lab_name}.yaml")

def main():
    lab_name = get_lab_name()
    routers = get_router_info()
    connections = get_connections(routers)
    prefix = get_prefix()
    template = get_eve_ng_template()
    image = get_eve_ng_image()
    subnets = generate_subnets(prefix, connections, routers)
    generate_unl_file(lab_name, routers, connections, subnets, template, image)

if __name__ == "__main__":
    main()