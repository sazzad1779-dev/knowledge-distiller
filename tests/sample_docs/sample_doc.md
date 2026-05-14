# Introduction to Distributed Systems

A distributed system is a collection of independent computers that appear to its users as a single coherent system.

## Concept 1: Transparency
Transparency is the extent to which a distributed system appears to the user as if it were a single system. There are several types of transparency:
- Access transparency: hide differences in data representation and how a resource is accessed.
- Location transparency: hide where a resource is located.
- Migration transparency: hide that a resource may move to another location.

Example: When you use a cloud storage service like Dropbox, you don't know (or need to know) which physical server your files are stored on. It appears as a single local folder.

## Concept 2: Scalability
Scalability is the ability of a system to handle a growing amount of work or its potential to be enlarged to accommodate that growth.
- Horizontal scalability (scaling out): adding more nodes to the system.
- Vertical scalability (scaling up): adding more resources (CPU, RAM) to an existing node.

Example: If a website starts getting more traffic, the owners might add five more web servers to handle the load. This is horizontal scaling.

## Concept 3: Fault Tolerance
Fault tolerance is the property that enables a system to continue operating properly in the event of the failure of one or more components.

Example: RAID 1 (mirroring) allows a computer to keep running even if one of the hard drives fails, because there is an identical copy on another drive.
