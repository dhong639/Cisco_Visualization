# Requirements

# Overview
## Default Values
## Calculating port types
## Assigning profiles
## Assigning settings

# Current Issues and Future Plans
## Parent Node and Horizontal Edge Determination
* Current model runs Dijkstra's from each node to the TOR
    * This is very costly and recalculates multiple subproblems
    * This was a very early requirement that should be deprecated
* Use either spanning-tree or breadth first
    * Both formulas would start at the root and work their way down
    * Spanning tree would enforce some link weights (LAGs) 
    * Breadth-first is only responsible for level-by-level traversal
    * Either way, the goal is to get a list of vertical links
* Calculating paths is not strictly necessary
    * graph object, labeled as id/Set() mappings, will return parent/child

## Storing Sites, the "everything" keyword
* The "everything" keyword is a user-friendly way to show every single site
    * this is non-negotiable
    * a user does not want to sift through 100+ site names
* currently, the "everything" keyword is stored inconveniently
    * stored as if it were an actual site
    * must be processed for the system to make sense

## Cytoscape Object
* There are ways to remove/add links and nodes without regenerating the whole graph
    * This is not necessarily going to look pretty
    * fcose must be used as the layout (standard breadth-first plays poorly)
* In terms of organization, the Cytoscape object should be its own class
    * the load_graph() function would be replaced with a different Graph object
    * could be integrated into existing graph object
        * existing graph is responsible for calculating link direction
        * existing graph is responsible for handling fabric and non-fabric links
* Whether or not animating content is better than regenerating the whole graph
    * regenerating fcose layout is to let customer know that a change was applied
    * animation would need to be loud and obvious
        * could point to exactly what was changed

## Overall Preview Structure
* This is the most complex and interconnected item
* Ideally, it would be mapped out so it's obvious where variables are accessed
* It might be beneficial to use JQuery to access and manage elements
