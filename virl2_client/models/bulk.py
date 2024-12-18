#
# This file is part of VIRL 2
# Copyright (c) 2019-2024, Cisco Systems, Inc.
# All rights reserved.
#
# Python bindings for the Cisco VIRL 2 Network Simulation Platform
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from __future__ import annotations

from typing import Any

import httpx

from virl2_client.models.lab import Lab
from virl2_client.utils import get_url_from_template

from .node import Node


class BulkManagement:
    _URL_TEMPLATES = {
        "nodes": "/nodes",
    }

    def __init__(self, labs: dict[str, Lab], session: httpx.Client) -> None:
        self._labs = labs
        self._session = session

    def _url_for(self, endpoint: str, **kwargs: dict):
        """
        Generate the URL for a given API endpoint.

        :param endpoint: The desired endpoint.
        :param **kwargs: Keyword arguments used to format the URL.
        :returns: The formatted URL.
        """
        return get_url_from_template(endpoint, self._URL_TEMPLATES, kwargs)

    def _handle_response(self, response: list[dict[str, Any]]) -> list[Node]:
        """
        Turn response into a list of Node objects.

        :param response: A list of dictionaries with node properties.
        :returns: A list of nodes objects.
        """
        result = []
        for data in response:
            # lab must exist (we may add support for local lab creation if needed)
            lab = self._labs[data.pop("lab_id")]
            node_id = data.pop("id")
            try:
                node = lab._nodes[node_id]
            except KeyError:
                # node is not fetched yet (can this even occur?)
                data["node_id"] = node_id
                # probably temporary until we unify responses
                data.pop("boot_progress")
                data.pop("state")
                node = lab._create_node_local(**data)
            result.append(node)
        return result

    def get_nodes(
        self,
        node_ids: list[str] | None = None,
        operational: bool | None = None,
        exclude_configurations: bool | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get details of the specified nodes (get all by default).

        Warning: All selected nodes must exist (support for partial results is not
            available yet).

        :param node_ids: An optional list of node IDs (none - get all nodes).
        :param operational: Whether to include operation data.
        :param exclude_configurations: Whether to exclude configurations.
        :returns: A list of dictionaries with node properties.
        """
        url = (
            f"{self._url_for('nodes')}?operational={operational}"
            f"&exclude_configurations={exclude_configurations}"
        )
        if node_ids:
            # https://github.com/encode/httpx/discussions/1587
            return self._session.request("GET", url, json=node_ids).json()
        else:
            return self._session.get(url).json()

    def fetch_nodes(
        self,
        node_ids: list[str] | None = None,
        operational: bool | None = None,
        exclude_configurations: bool | None = None,
    ) -> list[Node]:
        """
        Get details of the specified nodes (get all by default).

        Warning: All related labs must exist locally. Call ClientLibrary(...).all_labs()
            to fetch all labs.
        Warning: All selected nodes must exist (support for partial results is not
            available yet).

        :param node_ids: An optional list of node IDs (none - get all nodes).
        :param operational: Whether to include operation data.
        :param exclude_configurations: Whether to exclude configurations.
        :returns: A list of nodes objects.
        """
        response = self.get_nodes(
            node_ids=node_ids,
            operational=operational,
            exclude_configurations=exclude_configurations,
        )
        return self._handle_response(response)

    def post_nodes(
        self,
        node_data: list[dict],
        populate_interfaces=False,
    ) -> list[dict[str, Any]]:
        """
        Add the specified nodes.

        Warning: All data must be valid (support for partial results is not available
            yet).

        :param node_data: A list of dictionaries with node properties.
        :param populate_interfaces: Whether to automatically create node interfaces.
        :returns: A list of dictionaries with node properties.
        """
        url = f"{self._url_for('nodes')}?populate_interfaces={populate_interfaces}"
        return self._session.post(url, json=node_data).json()

    def create_nodes(
        self,
        node_data: list[dict],
        populate_interfaces=False,
    ) -> list[Node]:
        """
        Add the specified nodes.

        Warning: All updated labs must exist locally. Call ClientLibrary(...).all_labs()
            to fetch all labs.
        Warning: All data must be valid (support for partial results is not available
            yet).

        :param node_data: A list of dictionaries with node properties.
        :param populate_interfaces: Whether to automatically create node interfaces.
        :returns: A list of nodes objects.
        """
        response = self.post_nodes(
            node_data=node_data, populate_interfaces=populate_interfaces
        )
        return self._handle_response(response)

    def patch_nodes(self, node_data: list[dict]) -> list[dict[str, Any]]:
        """
        Update details for the specified nodes.

        Warning: All data must be valid (support for partial results is not available
            yet).

        :param node_data: A list of dictionaries with node updatable properties.
        :returns: A list of dictionaries with node properties.
        """
        url = self._url_for("nodes")
        return self._session.patch(url, json=node_data).json()

    def update_nodes(self, node_data: list[dict]) -> list[Node]:
        """
        Update details for the specified nodes.

        Warning: All updated labs must exist locally. Call ClientLibrary(...).all_labs()
            to fetch all labs.
        Warning: All data must be valid (support for partial results is not available
            yet).

        :param node_data: A list of dictionaries with node updatable properties.
        :returns: A list of nodes objects.
        """
        response = self.patch_nodes(node_data)
        # node.update() returns None
        return self._handle_response(response)

    def delete_nodes(self, node_ids: list[str]) -> None:
        """
        Delete the specified nodes (from the server only).

        Warning: All selected nodes must exist (support for partial results is not
            available yet).

        :param node_ids: A list of node IDs.
        :returns: None.
        """
        url = self._url_for("nodes")
        # https://github.com/encode/httpx/discussions/1587
        self._session.request("DELETE", url, json=node_ids)

    def remove_nodes(self, node_ids: list[str]) -> None:
        """
        Delete the specified nodes (both from the server and locally).

        Warning: All selected nodes must exist (support for partial results is not
            available yet).

        :param node_ids: A list of node IDs.
        :returns: None.
        """
        # this is performance-heavy and probably will be removed
        lab_nodes = [
            (lab, node)
            for lab in self._labs.values()
            for node_id, node in lab._nodes.items()
            if node_id in node_ids
        ]
        self.delete_nodes(node_ids)
        for lab, node in lab_nodes:
            lab._remove_node_local(node)
