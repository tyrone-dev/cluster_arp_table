# cluster_arp_table
Creates ARP Table for a Raspberry Pi Cluster automatically.

Master Node:
Sends out probe packets looking for slaves. 

Slave Node:
Listens for probe packets from Master.
Upon receipt: send slave hostname, IP, MAC to master

Master Node:
Construct ARP Table from Master and all Slave Node data
Optional: Send arp table via email
