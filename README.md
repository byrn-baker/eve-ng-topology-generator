# eve-ng-topology-generator
Provide input for how many routers, their names, and connections, an overall prefix to use for the point to points and the template and image to use in EVE and this should generate a topology for you. I've added another python script that takes the input from a yaml file for more complex topologies where it might be easier to manage the topology from a yaml. 

## Things to keep in mind
I've only tested this with IOL templates in EVE and I am only generating startup configs in the IOS fashion.

At some point I will figure out a better way to include more templates and get the interface names set appropriately as well. At this point I am pushing the limits of my abilities to code this, but as I learn I will update. 

## Example inputs for generate_unl.py
The YAML file will include the router names and their interfaces plus subnets. The UNL file includes a startup configuration with the hostname set and the interface addresses set.

```bash
$ python generate_unl.py
Enter lab name: test
Enter the router name prefix: R
Enter the number of routers: 6
Is R1 connected to R2? (y/n): y
Is R1 connected to R3? (y/n): y
Is R1 connected to R4? (y/n): y
Is R1 connected to R5? (y/n): y
Is R1 connected to R6? (y/n): y
Is R2 connected to R3? (y/n): y
Is R2 connected to R4? (y/n): y
Is R2 connected to R5? (y/n): y
Is R2 connected to R6? (y/n): y
Is R3 connected to R4? (y/n): y
Is R3 connected to R5? (y/n): y
Is R3 connected to R6? (y/n): y
Is R4 connected to R5? (y/n): y
Is R4 connected to R6? (y/n): y
Is R5 connected to R6? (y/n): y
Enter prefix (e.g., 10.0.0.0/16): 10.0.0.0/16
Enter EVE-NG template (e.g., iol): iol
Enter EVE-NG image (e.g., x86_64_crb_linux-adventerprisek9-ms.bin): x86_64_crb_linux-adventerprisek9-ms.bin
Setting network_id 1 for connection between R1 and R2
Setting network_id 2 for connection between R1 and R3
Setting network_id 3 for connection between R1 and R4
Setting network_id 4 for connection between R1 and R5
Setting network_id 5 for connection between R1 and R6
Setting network_id 6 for connection between R2 and R3
Setting network_id 7 for connection between R2 and R4
Setting network_id 8 for connection between R2 and R5
Setting network_id 9 for connection between R2 and R6
Setting network_id 10 for connection between R3 and R4
Setting network_id 11 for connection between R3 and R5
Setting network_id 12 for connection between R3 and R6
Setting network_id 13 for connection between R4 and R5
Setting network_id 14 for connection between R4 and R6
Setting network_id 15 for connection between R5 and R6
.unl file generated: test.unl
Interfaces for each router:
R1: ['e0/0', 'e0/1', 'e0/2', 'e0/3', 'e1/0']
R2: ['e0/0', 'e0/1', 'e0/2', 'e0/3', 'e1/0']
R3: ['e0/0', 'e0/1', 'e0/2', 'e0/3', 'e1/0']
R4: ['e0/0', 'e0/1', 'e0/2', 'e0/3', 'e1/0']
R5: ['e0/0', 'e0/1', 'e0/2', 'e0/3', 'e1/0']
R6: ['e0/0', 'e0/1', 'e0/2', 'e0/3', 'e1/0']
YAML file generated: test.yaml
```

Current output of the topology when copied to your EVE server
<img src="screenshots/topology.png" alt="">


What the startup configuration will look like
<img src="screenshots/startup_config.png" alt="">


## Example inputs for generate_unl_with_yaml.py
I've added some logic to ensure that the routers are placed in squares to help make the intial topology less messy. However there is some moving around and re-arranging you will have to do to fit your needs.

One small bug at this point if you have more than one interface between two routers it uses the same network_id for both interfaces on both routers. Trying to figure out how to fix this without breaking other stuff.
```bash
$ python gen_unl_with_yaml.py 
Enter the name for the lab: ccie-sp
Enter the name of the YAML file (including .yaml): ccie-sp-topo.yaml
UNL file 'ccie-sp.unl' has been generated with a unique UUID and network labels.
```
