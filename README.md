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
