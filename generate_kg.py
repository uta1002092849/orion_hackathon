import json
import random
import os

# Hyperparameters
SCHEMA_PATH = "input/schema.txt"
INSTANCES_PATH = "input/instances.json"
OUTPUT_PATH = "generated_kg.json"
CONNECTION_PROBABILITY = 0.5 # Probability [0, 1] that any valid pair is connected
SEED = 42

# Constraint Exceptions
# Relations where the Subject must be unique (One Subject -> Many Objects? No, Subject appears once).
# Example: (Person, bornIn, City). Each Person (Subject) born in at most one City.
UNIQUE_SUBJECT_RELATIONS = [
    # "(SubjectType, predicate, ObjectType)"
    # Add relations here where the Subject (first element) should only have one outgoing edge of this type.
]

# Relations where the Object must be unique (Many Subjects -> One Object? No, Object appears once).
# Example: (City, companyLocation, Company). Each Company (Object) located in at most one City.
UNIQUE_OBJECT_RELATIONS = [
    "(City,companyLocation,Company)",
    "(City,universityLocation,University)",
    "(State,stateOf,City)",
    "(University,hasCollege,College)",
    "(College,hasDepartment,Department)", 
    "(Department,offersCourse,Course)",
    "(Degree,degreeMajor,Major)",
    "(Degree,degreeLevel,DegreeLevel)",
    "(Course,courseSubject,Subject)"
]

def parse_schema(schema_path):
    # Return list of (SubjectType, predicate, ObjectType)
    relations = []
    try:
        with open(schema_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # format "(SubjectType, predicate, ObjectType)"
                if line.startswith('(') and line.endswith(')'):
                    content = line[1:-1]
                    parts = [p.strip() for p in content.split(',')]
                    if len(parts) == 3:
                        relations.append(tuple(parts))
    except Exception as e:
        print(f"Error reading schema: {e}")
    return relations

def generate_kg(schema_path, instances_path, output_path, probability, seed):
    if seed is not None:
        random.seed(seed)
    
    # relation here is a list of (SubjectType, predicate, ObjectType)
    relations = parse_schema(schema_path)
    if not relations:
        print("No relations found in schema.")
        return

    try:
        with open(instances_path, 'r') as f:
            # instances_data: NodeType -> List of Instance Labels
            instances_data = json.load(f)
    except Exception as e:
        print(f"Error reading instances: {e}")
        return

    kg_data = {}

    # iterate over each relation in the schema
    for subj_type, pred, obj_type in relations:
        key = f"({subj_type},{pred},{obj_type})"
        if subj_type not in instances_data:
            print(f"Warning: Subject Type '{subj_type}' for relation '{key}' not found in instances.")
            continue
        if obj_type not in instances_data:
            print(f"Warning: Object Type '{obj_type}' for relation '{key}' not found in instances.")
            continue
        
        # Index into instances_data to get lists of instances for subject and object types
        subjs = instances_data[subj_type]
        objs = instances_data[obj_type]
        
        edge_list = []
        
        # Check constraints
        if key in UNIQUE_OBJECT_RELATIONS:
            # Each Object connects to at most one Subject
            # Iterate through Objects
            for o in objs:
                # Decide if this object should be connected at all based on probability?
                # Or probability determines *which* subject?
                # Let's say with probability p, it gets connected to ONE random subject.
                if random.random() < probability:
                    s = random.choice(subjs)
                    edge_val = f"({s},{pred},{o})"
                    edge_list.append(edge_val)
                    
        elif key in UNIQUE_SUBJECT_RELATIONS:
            # Each Subject connects to at most one Object
            # Iterate through Subjects
            for s in subjs:
                if random.random() < probability:
                    o = random.choice(objs)
                    edge_val = f"({s},{pred},{o})"
                    edge_list.append(edge_val)
        
        else:
            # Default: Probabilistic connection (Many-to-Many potential)
            # Check every possible pair (s, o) and connect with probability p
            for s in subjs:
                for o in objs:
                    if random.random() < probability:
                        # Format: "(SubjectInstance,predicate,ObjectInstance)"
                        edge_val = f"({s},{pred},{o})"
                        edge_list.append(edge_val)
        
        kg_data[key] = edge_list

    # Ensure output directory exists if path contains directories
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_path, 'w') as f:
        json.dump(kg_data, f, indent=4)
    print(f"Successfully generated KG at {output_path} with probability {probability}")

def main():
    if not os.path.exists(SCHEMA_PATH):
        print(f"Error: Schema file not found at {SCHEMA_PATH}")
        return
    if not os.path.exists(INSTANCES_PATH):
        print(f"Error: Instances file not found at {INSTANCES_PATH}")
        return

    generate_kg(SCHEMA_PATH, INSTANCES_PATH, OUTPUT_PATH, CONNECTION_PROBABILITY, SEED)

if __name__ == "__main__":
    main()
