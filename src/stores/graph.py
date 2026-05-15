from neo4j import GraphDatabase


class GraphStore:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def upsert_entity(self, name: str, entity_type: str, chunk_ids: list[str]) -> None:
        with self.driver.session() as session:
            session.run(
                """
                MERGE (e:Entity {name: $name, type: $type})
                SET e.chunk_ids = coalesce(e.chunk_ids, []) + $chunk_ids
                """,
                name=name, type=entity_type, chunk_ids=chunk_ids,
            )

    def upsert_relationship(
        self, from_name: str, to_name: str, rel_type: str, chunk_id: str
    ) -> None:
        with self.driver.session() as session:
            session.run(
                """
                MERGE (a:Entity {name: $from_name})
                MERGE (b:Entity {name: $to_name})
                MERGE (a)-[r:RELATES {type: $rel_type}]->(b)
                SET r.chunk_ids = coalesce(r.chunk_ids, []) + [$chunk_id]
                """,
                from_name=from_name, to_name=to_name, rel_type=rel_type, chunk_id=chunk_id,
            )

    def find_entity(self, name: str) -> dict | None:
        with self.driver.session() as session:
            result = session.run(
                "MATCH (e:Entity {name: $name}) RETURN e", name=name
            ).single()
        return dict(result["e"]) if result else None

    def clear(self) -> None:
        """Wipe the graph. Useful during development."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")