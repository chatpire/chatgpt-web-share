def get_model_name_from_conv(conversation) -> str:
    result = None
    try:
        current_node = conversation["current_node"]
        while current_node:
            node = conversation["mapping"][current_node]
            result = node["message"]["metadata"]["model_slug"]
            if result:
                break
            current_node = node["parent"]
    finally:
        return result
