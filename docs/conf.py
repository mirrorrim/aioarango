project = "aioarango"
copyright = "2016-2021, Joohwan Oh, Alexey Tylindus"
author = "Joohwan Oh & Alexey Tylindus"
extensions = [
    "sphinx_rtd_theme",
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.viewcode",
]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
html_static_path = ["static"]
html_theme = "sphinx_rtd_theme"
master_doc = "index"

autodoc_member_order = "bysource"

doctest_global_setup = """
from aioarango import ArangoClient
# Initialize the ArangoDB client.
client = ArangoClient()
# Connect to "_system" database as root user.
sys_db = await client.db('_system', username='root', password='passwd')
# Create "test" database if it does not exist.
if not await sys_db.has_database('test'):
    await sys_db.create_database('test')
# Ensure that user "johndoe@gmail.com" does not exist.
if await sys_db.has_user('johndoe@gmail.com'):
    await sys_db.delete_user('johndoe@gmail.com')
# Connect to "test" database as root user.
db = await client.db('test', username='root', password='passwd')
# Create "students" collection if it does not exist.
if await db.has_collection('students'):
    await db.collection('students').truncate()
else:
    await db.create_collection('students')
# Ensure that "cities" collection does not exist.
if await db.has_collection('cities'):
    await db.delete_collection('cities')
# Create "school" graph if it does not exist.
if await db.has_graph("school"):
    school = db.graph('school')
else:
    await school = db.create_graph('school')
# Create "teachers" vertex collection if it does not exist.
if await school.has_vertex_collection('teachers'):
    await school.vertex_collection('teachers').truncate()
else:
    await school.create_vertex_collection('teachers')
# Create "lectures" vertex collection if it does not exist.
if await school.has_vertex_collection('lectures'):
    await school.vertex_collection('lectures').truncate()
else:
    await school.create_vertex_collection('lectures')
# Create "teach" edge definition if it does not exist.
if await school.has_edge_definition('teach'):
    await school.edge_collection('teach').truncate()
else:
    await school.create_edge_definition(
        edge_collection='teach',
        from_vertex_collections=['teachers'],
        to_vertex_collections=['lectures']
    )
"""
