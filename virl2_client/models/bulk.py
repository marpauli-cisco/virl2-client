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

import httpx

from virl2_client.utils import get_url_from_template

from .node import Node


class BulkManagement:
    _URL_TEMPLATES = {
        "nodes": "/nodes",
    }

    def __init__(self, session: httpx.Client) -> None:
        self._session = session

    def _url_for(self, endpoint: str, **kwargs: dict):
        """
        Generate the URL for a given API endpoint.

        :param endpoint: The desired endpoint.
        :param **kwargs: Keyword arguments used to format the URL.
        :returns: The formatted URL.
        """
        return get_url_from_template(endpoint, self._URL_TEMPLATES, kwargs)

    def get_nodes(
        self,
        node_ids: list[str] | None = None,
        operational: bool | None = None,
        exclude_configurations: bool | None = None,
    ) -> list[Node]:
        """
        Get details of the specified nodes (get all by default).

        :returns: A list of nodes objects.
        """
        url = (
            f"{self._url_for('nodes')}?operational={operational}"
            f"&exclude_configurations={exclude_configurations}"
        )
        if node_ids:
            return self._session.get(url, json=node_ids).json()
        else:
            return self._session.get(url).json()

    def post_nodes(
        self,
        node_data: list[dict],
        populate_interfaces=False,
    ) -> list[Node]:
        """
        Add the specified nodes.

        :returns: A list of nodes objects.
        """
        url = f"{self._url_for('nodes')}?populate_interfaces={populate_interfaces}"
        return self._session.post(url, json=node_data).json()

    def patch_nodes(self, node_data: list[dict]) -> list[Node]:
        """
        Update details for the specified nodes.

        :returns: A list of nodes objects.
        """
        url = self._url_for("nodes")
        return self._session.patch(url, json=node_data).json()

    def delete_nodes(self, node_ids: list[str]) -> None:
        """
        Delete the specified nodes.

        :returns: None.
        """
        url = self._url_for("nodes")
        # https://github.com/encode/httpx/discussions/1587
        self._session.request("DELETE", url, json=node_ids)
