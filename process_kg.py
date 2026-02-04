import json
import argparse
import os
import hashlib

VERBOSE = False

def parse_triple_string(s):
    """Parses a string like '(A,b,C)' into a tuple (A, b, C)."""
    s = s.strip()
    if s.startswith('(') and s.endswith(')'):
        s = s[1:-1]
    parts = s.split(',')
    # Strip whitespace from parts just in case
    return [p.strip() for p in parts]

def get_id(item, mapping):
    """Gets a unique ID for an item using hash, adding it to the mapping if new."""
    if item not in mapping:
        # Use MD5 hash converted to integer
        mapping[item] = int(hashlib.md5(item.encode('utf-8')).hexdigest(), 16)
    return mapping[item]

def main():
    parser = argparse.ArgumentParser(description="Process Academic Knowledge Graph JSON.")
    parser.add_argument("input_file", help="Path to the input JSON file.")
    args = parser.parse_args()

    input_path = args.input_file

    if not os.path.exists(input_path):
        print(f"Error: File not found at {input_path}")
        return

    try:
        with open(input_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return

    # Mappings
    node_type_map = {}
    edge_type_map = {}
    instance_map = {}

    # Result container: Node Type ID -> Set of Instance IDs
    node_type_instances = {}
    # Result container: Node Type Label -> Set of Instance Labels
    node_type_instances_labels = {}

    for key_pattern, instance_list in data.items():
        # Parse the key: "(SubjectType,predicate,ObjectType)"
        parts = parse_triple_string(key_pattern)
        if len(parts) != 3:
            print(f"Warning: Skipping malformed key '{key_pattern}'")
            continue
        
        subj_type_str, edge_type_str, obj_type_str = parts

        # Get IDs for types
        subj_type_id = get_id(subj_type_str, node_type_map)
        obj_type_id = get_id(obj_type_str, node_type_map)
        edge_type_id = get_id(edge_type_str, edge_type_map)

        # Initialize list in result dict if needed
        if subj_type_id not in node_type_instances:
            node_type_instances[subj_type_id] = set()
        if obj_type_id not in node_type_instances:
            node_type_instances[obj_type_id] = set()

        if subj_type_str not in node_type_instances_labels:
            node_type_instances_labels[subj_type_str] = set()
        if obj_type_str not in node_type_instances_labels:
            node_type_instances_labels[obj_type_str] = set()

        for instance_str in instance_list:
            # Parse the instance: "(SubjectInstance,predicate,ObjectInstance)"
            inst_parts = parse_triple_string(instance_str)
            if len(inst_parts) != 3:
                print(f"Warning: Skipping malformed instance string '{instance_str}' in key '{key_pattern}'")
                continue
            
            subj_inst_str, pred_inst_str, obj_inst_str = inst_parts

            # Get IDs for instances
            subj_inst_id = get_id(subj_inst_str, instance_map)
            obj_inst_id = get_id(obj_inst_str, instance_map)

            # Associate instances with their types
            if subj_inst_id in node_type_instances[subj_type_id]:
                if VERBOSE:
                    print(f"Duplicate instance detected: '{subj_inst_str}' for node type '{subj_type_str}'")
            node_type_instances[subj_type_id].add(subj_inst_id)
            node_type_instances_labels[subj_type_str].add(subj_inst_str)

            if obj_inst_id in node_type_instances[obj_type_id]:
                if VERBOSE:
                    print(f"Duplicate instance detected: '{obj_inst_str}' for node type '{obj_type_str}'")
            node_type_instances[obj_type_id].add(obj_inst_id)
            node_type_instances_labels[obj_type_str].add(obj_inst_str)

    # Convert sets to sorted lists for JSON serialization
    final_node_instances = {k: sorted(list(v)) for k, v in node_type_instances.items()}
    final_node_instances_labels = {k: sorted(list(v)) for k, v in node_type_instances_labels.items()}

    # Output filenames
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    f_node_map = os.path.join(output_dir, "map_node_types.json")
    f_edge_map = os.path.join(output_dir, "map_edge_types.json")
    f_inst_map = os.path.join(output_dir, "map_instances.json")
    f_final = os.path.join(output_dir, "node_type_instances.json")
    f_final_labels = os.path.join(output_dir, "node_type_instances_labels.json")

    # Write files
    print("Writing output files...")
    
    with open(f_node_map, 'w') as f:
        json.dump(node_type_map, f, indent=4)
    print(f"Created {f_node_map}")

    with open(f_edge_map, 'w') as f:
        json.dump(edge_type_map, f, indent=4)
    print(f"Created {f_edge_map}")

    with open(f_inst_map, 'w') as f:
        json.dump(instance_map, f, indent=4)
    print(f"Created {f_inst_map}")

    with open(f_final, 'w') as f:
        json.dump(final_node_instances, f, indent=4)
    print(f"Created {f_final}")

    with open(f_final_labels, 'w') as f:
        json.dump(final_node_instances_labels, f, indent=4)
    print(f"Created {f_final_labels}")

    print("Processing complete.")

if __name__ == "__main__":
    main()
