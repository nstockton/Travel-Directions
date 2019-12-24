# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# The manifest will be inserted as a resource into the executable.
# This gives the controls the Windows XP appearance (if run on XP)
MANIFEST_TEMPLATE = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
<assemblyIdentity
	version="5.0.0.0"
	processorArchitecture="x86"
	name="%(prog)s"
	type="win32"
/>
<description>%(prog)s Program</description>
<trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
	<security>
		<requestedPrivileges>
			<requestedExecutionLevel
				level="asInvoker"
				uiAccess="false">
			</requestedExecutionLevel>
		</requestedPrivileges>
	</security>
</trustInfo>
<dependency>
	<dependentAssembly>
		<assemblyIdentity
			type="win32"
			name="Microsoft.VC90.CRT"
			version="9.0.21022.8"
			processorArchitecture="x86"
			publicKeyToken="1fc8b3b9a1e18e3b">
		</assemblyIdentity>
	</dependentAssembly>
</dependency>
<dependency>
	<dependentAssembly>
		<assemblyIdentity
			type="win32"
			name="Microsoft.Windows.Common-Controls"
			version="6.0.0.0"
			processorArchitecture="X86"
			publicKeyToken="6595b64144ccf1df"
			language="*"
		/>
	</dependentAssembly>
</dependency>
</assembly>
""".lstrip()

RT_MANIFEST = 24
