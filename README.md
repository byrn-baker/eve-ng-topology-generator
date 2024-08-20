# eve-ng-topology-generator
Provide input for how many routers, their names, and connections, an overall prefix to use for the point to points and the template and image to use in EVE and this should generate a topology for you.

The YAML file will include the router names and their interfaces plus IPs as well. 


## Things to add.
I've really only tested this with IOL so I need to make some updates or selection on interface names at some point



## Example inputs
```bash
Enter lab name: py-test
Enter the number of routers: 4
Enter router 1 name: R1
Enter router 2 name: R2
Enter router 3 name: R3
Enter router 4 name: R4 
Is R1 connected to R2? (y/n): y
Is R1 connected to R3? (y/n): y
Is R1 connected to R4? (y/n): n
Is R2 connected to R3? (y/n): n
Is R2 connected to R4? (y/n): y
Is R3 connected to R4? (y/n): y
Enter prefix (e.g., 10.0.0.0/16): 10.1.0.0/16
Enter EVE-NG template (e.g., iol): iol
Enter EVE-NG image (e.g., x86_64_crb_linux-adventerprisek9-ms.bin): x86_64_crb_linux-adventerprisek9-ms.bin 
.unl file generated: py-test.unl
YAML file generated: py-test.yaml
```