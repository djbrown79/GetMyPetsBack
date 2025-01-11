import os
from collections import defaultdict
import amulet
import math
import path

# Replace with your actual UUID mappings
BEDROCK_TO_JAVA_UUID_MAP = {
    "b7f0091a-cd63-4c39-9595-67aecad1eea2": "b7348eff-4c5e-47e7-8812-90a7ba3d1b21",
    # ...
}

# IMPORTANT: Unlike anvil-parser, Amulet expects the *world folder* that contains level.dat,
# not just the region folder. So point this to your overall world folder.
WORLD_FOLDER_PATH = r"R:\ROBLOX_ GAME OF QUALITY"

def iterate_chunks_within_radius(center_x, center_z, radius):
    """
    Iterates over all *chunk* coords within or on the edge of a circular radius
    (all math here in chunk coordinates).
    """
    for chunk_x in range(center_x - radius, center_x + radius + 1):
        for chunk_z in range(center_z - radius, center_z + radius + 1):
            dist_sq = (chunk_x - center_x)**2 + (chunk_z - center_z)**2
            if dist_sq <= radius**2:
                yield chunk_x, chunk_z

def fix_pet_uuids_in_world(world_path, uuid_map, center_x, center_z, radius):
    """
    Loads the Minecraft world using Amulet, then for each chunk in [center_x ± radius, center_z ± radius]
    attempts to load the chunk, inspects the living entities, and updates OwnerUUID if needed.
    """
    print(f"Loading world at {world_path}")
    level = amulet.load_level(world_path)

    # Typically, dimension=amulet.OVERWORLD for the Overworld
    dimension = amulet.dimensions.OVERWORLD

    # Gather all chunk coordinates in our chosen radius
    chunk_coords = list(iterate_chunks_within_radius(center_x, center_z, radius))

    changed_any_chunk = False

    # For each chunk, we attempt to load it from the world
    for (cx, cz) in chunk_coords:
        # load_chunk returns (chunk, _), or it may throw an error
        try:
            chunk, _ = level.load_chunk(cx, cz, dimension)
        except Exception as e:
            # If the chunk doesn't exist or can't be read
            print(f"Skipping chunk ({cx},{cz}): {e}")
            continue

        # If chunk.entities is empty, there's no living entity stored in that chunk.
        if not chunk.entities:
            continue

        print(f"  Checking chunk ({cx},{cz}) for entities...")
        changed_this_chunk = False

        # Amulet represents entities as a list of tuples: (entity_id, nbt_data)
        # entity_nbt is an NBT object (similar to 'TAG_Compound'), so we can do:
        #   if "OwnerUUID" in entity_nbt:
        #       ...
        for entity_id, entity_nbt in chunk.entities:
            # You can see the entire entity structure if you want:
            # print(entity_nbt.pretty_tree())

            if "OwnerUUID" in entity_nbt:
                old_uuid = entity_nbt["OwnerUUID"].value
                if old_uuid in uuid_map:
                    new_uuid = uuid_map[old_uuid]
                    entity_nbt["OwnerUUID"].value = new_uuid
                    print(f"    Updated entity at chunk ({cx},{cz}): {old_uuid} -> {new_uuid}")
                    changed_this_chunk = True

        if changed_this_chunk:
            changed_any_chunk = True
            # Write updated chunk data back to the in-memory world
            #level.save_chunk(cx, cz, dimension)

    if changed_any_chunk:
        print("Saving updated chunks to disk...")
        # Actually write all in-memory changes out to the world folder
        #level.save()
    else:
        print("No changes were made.")

    level.close()

def main():
    # Because we’re now using Amulet, we must point to the *entire world folder*,
    # not just the region folder. So we pass WORLD_FOLDER_PATH to fix_pet_uuids_in_world
    fix_pet_uuids_in_world(
        world_path=WORLD_FOLDER_PATH,
        uuid_map=BEDROCK_TO_JAVA_UUID_MAP,
        center_x=340,   # chunk coordinate
        center_z=319,   # chunk coordinate
        radius=20
    )
    print("Done!")

if __name__ == "__main__":
    main()
