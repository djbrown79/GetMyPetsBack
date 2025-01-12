import amulet
import numpy as np
import uuid
from amulet_nbt import StringTag


BEDROCK_TO_JAVA_UUID_MAP = {
    "PeppyBunion" : { "b7f0091a-cd63-4c39-9595-67aecad1eea2" : "b7348eff-4c5e-47e7-8812-90a7ba3d1b21" },
    # ...
}


WORLD_FOLDER_PATH = r"D:\ModrinthApp\profiles\Vanilla Chunk Loader\saves\ROBLOX - JAVA"


def iterate_chunks_within_radius(center_x, center_z, radius):
    """
    Iterates over all *chunk* coords within or on the edge of a circular radius
    (all math here in chunk coordinates).
    """
    for chunk_x in range(center_x - radius, center_x + radius + 1):
        for chunk_z in range(center_z - center_z, center_z + radius + 1):
            dist_sq = (chunk_x - center_x) ** 2 + (chunk_z - center_z) ** 2
            if dist_sq <= radius ** 2:
                yield chunk_x, chunk_z


def minecraft_uuid_from_ints(arr):
    i0, i1, i2, i3 = arr.tolist()
    msb = (i0 & 0xffffffff) << 32 | (i1 & 0xffffffff)
    lsb = (i2 & 0xffffffff) << 32 | (i3 & 0xffffffff)
    return str(uuid.UUID(int=(msb << 64 | lsb)))


def format_uuid_display(uuid_obj):
    """Format UUID for display"""
    return f"UUID: {str(uuid_obj)}"


def uuid_str_to_ints(uuid_str):
    """Convert a UUID string to Minecraft's int array format"""
    u = uuid.UUID(uuid_str)
    # Split into two 64-bit numbers and then into four 32-bit numbers
    msb = u.int >> 64
    lsb = u.int & ((1 << 64) - 1)
    return [
        (msb >> 32) & 0xFFFFFFFF,
        msb & 0xFFFFFFFF,
        (lsb >> 32) & 0xFFFFFFFF,
        lsb & 0xFFFFFFFF
    ]


def fix_pet_uuids_in_world(world_path, uuid_map, center_x, center_z, radius):
    """
    Loads the Minecraft world using Amulet, then for each chunk in [center_x ± radius, center_z ± radius]
    attempts to load the entities, and updates OwnerUUID if needed.
    """
    print(f"Loading world at {world_path}")
    level = amulet.load_level(world_path)

    # Typically, dimension=amulet.OVERWORLD for the Overworld
    dimension = "minecraft:overworld"

    # Gather all chunk coordinates in our chosen radius
    chunk_coords = list(iterate_chunks_within_radius(center_x, center_z, radius))

    changed_any_chunk = False

    # For each chunk, we attempt to load its entities from the world
    for (cx, cz) in chunk_coords:
        try:
            entities, _ = level.get_native_entities(cx, cz, dimension)
        except Exception as e:
            # If the chunk doesn't exist or can't be read
            print(f"Skipping chunk ({cx},{cz}): {e}")
            continue

        # If chunk.entities is empty, there's no living entity stored in that chunk.
        if not entities:
            continue

        changed_this_chunk = False

        for entity in entities:
            entity_nbt = entity.nbt

            if entity.base_name != "wolf":
                continue

            if 'Owner' in entity_nbt.compound:
                owner_tag = entity_nbt.compound['Owner']
                old_uuid_data = owner_tag.py_data
                if isinstance(old_uuid_data, np.ndarray) and old_uuid_data.size == 4:
                    old_uuid = uuid.UUID(bytes=old_uuid_data.tobytes())
                else:
                    old_uuid = uuid.UUID(old_uuid_data)

                print(f"  Found entity with owner ({cx},{cz}): {format_uuid_display(old_uuid)}")

                target_uuid = uuid.UUID("bc0b2f8f-f094-4386-ba6e-6702b7f255d4")
                print(f"  Target {format_uuid_display(target_uuid)}")
                entity_nbt.compound["Owner"] = StringTag(str(target_uuid))
                print(f"    Updated entity at chunk ({cx},{cz}): {old_uuid} -> {target_uuid}")


                changed_this_chunk = True

        if changed_this_chunk:
            changed_any_chunk = True

            entity.changed = True

            # Write updated entity data back to the in-memory world
            level.set_native_entites(cx, cz, dimension, entities)

    if changed_any_chunk:
        print("Saving updated entities to disk...")
        # Actually write all in-memory changes out to the world folder
        level.save()
    else:
        print("No changes were made.")

    level.close()


def main():
    # Because we’re now using Amulet, we must point to the *entire world folder*,
    # not just the region folder. So we pass WORLD_FOLDER_PATH to fix_pet_uuids_in_world
    fix_pet_uuids_in_world(
        world_path=WORLD_FOLDER_PATH,
        uuid_map=BEDROCK_TO_JAVA_UUID_MAP,
        center_x=340,  # chunk coordinate
        center_z=319,  # chunk coordinate
        radius=5
    )
    print("Done!")


if __name__ == "__main__":
    main()