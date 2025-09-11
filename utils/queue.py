# import aio_pika
# import json
# from config import settings
# from utils.logger import log

# async def publish_message(queue_name: str, message_body: dict):
#     try:
#         connection = await aio_pika.connect_robust(settings.rabbitmq_url)
#         async with connection:
#             channel = await connection.channel()
#             await channel.declare_queue(queue_name, durable=True) 

#             message = aio_pika.Message(
#                 body=json.dumps(message_body).encode(),
#                 delivery_mode=aio_pika.DeliveryMode.PERSISTENT
#             )

#             await channel.default_exchange.publish(message, routing_key=queue_name)
#             log.info(f"Successfully published message to queue '{queue_name}'")
#     except Exception:
#         log.exception(f"Failed to publish message to queue '{queue_name}'")