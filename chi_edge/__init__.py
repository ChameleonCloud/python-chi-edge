# Copyright 2021 University of Chicago
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

SUPPORTED_DEVICE_TYPES = (
    "raspberrypi",
    "nano",
)

# TODO(jason): this is a bit gross, but I'm not sure what the better option
# is. SDK users don't really need to care about this.
VIRTUAL_SITE_INTERNAL_ADDRESS = "10.20.111.10"
