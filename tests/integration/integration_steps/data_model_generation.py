import pandas as pd
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from cognite.client.data_classes.data_modeling import (
    DataModel,
    DataModelApply,
    EdgeApply,
    NodeApply,
    NodeOrEdgeData,
    SingleHopConnectionDefinition,
    Space,
    SpaceApply,
    View,
    ViewList,
)
from cognite.client.data_classes.data_modeling.ids import DataModelId, ViewId
from cognite.client.data_classes.data_modeling.instances import EdgeApplyList, InstancesResult, NodeApplyList

RESOURCES = Path(__file__).parent / "resources"

@dataclass
class ID:
    """
    Identifier used to create an external id based on
    columns in a dataframe. The ID will be "[prefix]:[column1]:[column2]:..."
    """

    prefix: str
    columns: list[str]

    def create(self, row: pd.Series) -> str:
        return (":".join([self.prefix] + [str(row[c]) for c in self.columns])).replace(" ", "_").lower()
    
@dataclass
class DirectID(ID):
    field_name: str


@dataclass
class NodeSource:
    view_id: str
    csv_path: Path
    id: ID
    properties: list[str]
    direct_relations: list[DirectID] = field(default_factory=list)

NODE_SOURCES = [
    NodeSource("Movie", RESOURCES / "movies.csv", ID("movie", ["title"]), ["title", "releaseYear", "runTimeMinutes"]),
    NodeSource("Person", RESOURCES / "persons.csv", ID("person", ["name"]), ["name", "birthYear"]),
    NodeSource(
        "Actor",
        RESOURCES / "actors.csv",
        ID("actor", ["personName"]),
        ["wonOscar"],
        [DirectID("person", ["personName"], "person")],
    ),
]

@dataclass
class EdgeSource:
    view_id: str
    field_name: str
    start: ID
    end: ID
    csv_path: Path

EDGE_SOURCES = [
    EdgeSource(
        "Person",
        "roles",
        ID("person", ["personName"]),
        ID("actor", ["personName"]),
        RESOURCES / "relation_actors_movies.csv",
    ),
    EdgeSource(
        "Movie", "actors", ID("movie", ["movie"]), ID("actor", ["personName"]), RESOURCES / "relation_actors_movies.csv"
    ),
    EdgeSource(
        "Actor", "movies", ID("actor", ["personName"]), ID("movie", ["movie"]), RESOURCES / "relation_actors_movies.csv"
    ),
]

def read_nodes(views: ViewList) -> NodeApplyList:
    nodes: list[NodeApply] = []
    for source in NODE_SOURCES:
        df = pd.read_csv(source.csv_path).infer_objects()
        view = cast(View, views.get(external_id=source.view_id))
        for _, row in df.iterrows():
            external_id = source.id.create(row)

            node = NodeApply(
                space=view.space,
                external_id=external_id,
                sources=[
                    NodeOrEdgeData(
                        source=view.as_id(),
                        properties={
                            **row[source.properties].to_dict(),
                            **{
                                direct.field_name: {"space": view.space, "externalId": direct.create(row)}
                                for direct in source.direct_relations
                            },
                        },
                    )
                ],
            )
            nodes.append(node)
    return NodeApplyList(nodes)


def read_edges(views: ViewList) -> EdgeApplyList:
    edges: list[EdgeApply] = []
    for source in EDGE_SOURCES:
        df = pd.read_csv(source.csv_path).infer_objects()
        df = df[list(set(source.start.columns + source.end.columns))].drop_duplicates()
        view = cast(View, views.get(external_id=source.view_id))
        for _, row in df.iterrows():
            start_ext_id = source.start.create(row)
            end_ext_id = source.end.create(row)
            type_ext_id = cast(SingleHopConnectionDefinition, view.properties[source.field_name]).type.external_id
            edge = EdgeApply(
                space=view.space,
                external_id=f"{start_ext_id}:{end_ext_id}",
                type=(view.space, type_ext_id),
                start_node=(view.space, start_ext_id),
                end_node=(view.space, end_ext_id),
            )
            edges.append(edge)
    return EdgeApplyList(edges)