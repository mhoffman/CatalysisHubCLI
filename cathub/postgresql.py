import psycopg2

set_schema = 'SET search_path TO stage;'

init_commands = [
    """CREATE TABLE publication (
    id SERIAL PRIMARY KEY,
    pub_id text UNIQUE,
    title text,
    authors jsonb,
    journal text,
    volume text,
    number text,
    pages text,
    year smallint,
    publisher text,
    doi text,
    tags jsonb
    );""",

    """CREATE TABLE publication_system (
    ase_id text REFERENCES systems(unique_id) ON DELETE CASCADE,
    pub_id text REFERENCES publication(pub_id) ON DELETE CASCADE,
    PRIMARY KEY (pub_id, ase_id)
    );""",

    """CREATE TABLE reaction (
    id SERIAL PRIMARY KEY, 
    chemical_composition text,
    surface_composition text,
    facet text,
    sites text,
    reactants jsonb,
    products jsonb,
    reaction_energy numeric,
    activation_energy numeric,
    dft_code text,
    dft_functional text,
    username text,
    pub_id text REFERENCES publication (pub_id) ON DELETE CASCADE
    );""",

    """CREATE TABLE reaction_system (
    name text, 
    ase_id text REFERENCES systems(unique_id) ON DELETE CASCADE,
    reaction_id integer REFERENCES reaction(id) ON DELETE CASCADE,
    PRIMARY KEY (reaction_id, ase_id)
    )"""
]

    
index_statements = [
    'CREATE INDEX idxpubid ON publication (pub_id);',
    'CREATE INDEX idxreacten ON reaction (reaction_energy);',
    'CREATE INDEX idxchemcomp ON reaction (chemical_composition);',
    'CREATE INDEX idxreact ON reaction USING GIN (reactants);',
    'CREATE INDEX idxprod ON reaction USING GIN (products);',
    'CREATE INDEX idxuser ON reaction (username);'
]

tsvector_statements = [
    """ALTER TABLE publication ADD COLUMN pubtextsearch tsvector;""",
    
    
    #"""CREATE TRIGGER tsvectorupdatepub BEFORE INSERT OR UPDATE
    #ON publication FOR EACH ROW EXECUTE PROCEDURE
    #UPDATE publication SET pubtextsearch = 
    #to_tsvector('english', coalesce(title, '') || ' ' || 
    #coalesce(authors::text, '') || ' ' || coalesce(year::text, '') || ' ' ||
    #coalesce(tags::text, ''))
    #;""",

    #     tsvector_update_trigger(pubtextsearch, 'pg_catalog.english', title, authors, year, tags)

    """ALTER TABLE reaction ADD COLUMN textsearch tsvector;""",
    
    
    #"""CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
    #ON reaction FOR EACH ROW EXECUTE PROCEDURE
    #tsvector_update_trigger(textsearch, 'pg_catalog.english', chemical_compotision, facet, reactants, products);""",

    'CREATE INDEX idxsearch ON reaction USING GIN (textsearch);'
    ]
tsvector_update = [
    """UPDATE publication SET pubtextsearch = 
    to_tsvector('simple', coalesce(title, '') || ' ' || 
    coalesce(authors::text, '') || ' ' || coalesce(year::text, '') || ' ' ||
    coalesce(tags::text, ''));
    """,

    """
    UPDATE reaction SET textsearch = 
    to_tsvector('simple', coalesce(regexp_replace(regexp_replace(chemical_composition, '([0-9])', '', 'g'), '()([A-Z])', '\1 \2','g'), '') || ' ' || 
    coalesce(facet, '') || ' ' || replace(replace(coalesce(reactants::text, '') || ' ' ||
    coalesce(products::text, ''), 'star',''), 'gas', ''));
    """
    ]


class CathubPostgreSQL:
    def __init__(self):
        self.initialized = False
        self.connection = None
        self.id = None

    def _connect(self):
        import os
        password = os.environ['DB_PASSWORD']
        con = psycopg2.connect(host="catappdatabase.cjlis1fysyzx.us-west-1.rds.amazonaws.com", 
                               user='catappuser',
                               password=password,
                               port=5432,
                               database='catappdatabase')
        
        return con

    def __enter__(self):
        assert self.connection is None
        self.connection = self._connect()
        return self

    def __exit__(self, exc_type):#, exc_value, tb):
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        self.connection.close()
        self.connection = None

    def _initialize(self, con):
        if self.initialized:
            return
        cur = con.cursor()
        
        cur.execute(set_schema)
        
        from ase.db.postgresql import PostgreSQLDatabase
        PostgreSQLDatabase()._initialize(con)
        
        cur.execute("""SELECT to_regclass('publication');""")
        if cur.fetchone()[0] == None:  # publication doesn't exist
            for init_command in init_commands:
                print init_command
                cur.execute(init_command)
            for statement in index_statements:
                print statement
                cur.execute(statement)
            for statement in tsvector_statements:
                print statement
                cur.execute(statement)   
            con.commit()
        self.initialized = True
        return self

    def drop_tables(self):
        con = self.connection or self._connect()
        self._initialize(con)
        cur = con.cursor()
        cur.execute("drop table reaction_system, reaction, publication_system, publication, text_key_values, number_key_values, information, species, systems;")
        con.commit()
        con.close()
        return

    def status(self):
        con = self.connection or self._connect()
        self._initialize(con)
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) from reaction;")
        print cur.fetchall()
        #cur.execute("""SELECT reactants, products FROM reaction where reference""")
        #print len(cur.fetchall())
 
    def write_publication(self, pub_values):
        con = self.connection or self._connect()
        self._initialize(con)
        cur = con.cursor()
        pub_id =  pub_values[1].encode('ascii','ignore')
        cur.execute("""SELECT id from publication where pub_id='{}'""".format(pub_id))
        row = cur.fetchone()
        if row is not None: #len(row) > 0:
            id = row#[0]
        else:
            key_str, value_str = get_key_value_str(pub_values, 'publication')
            insert_command = 'INSERT INTO publication ({}) VALUES ({}) RETURNING id;'.format(key_str, value_str)

            cur.execute(insert_command)
            id = cur.fetchone()[0]
    
        if self.connection is None:
            con.commit()
            con.close()
        return id, pub_id


    def write(self, values, table='reaction'):

        con = self.connection or self._connect()
        self._initialize(con)
        cur = con.cursor()

        #id = self.get_last_id(cur)
        #if self.id is None:
        #    id = self.get_last_id(cur) + 1
        #else:
        #    id = self.
        key_str, value_str = get_key_value_str(values, table)
        
        insert_command = 'INSERT INTO {} ({}) VALUES ({}) RETURNING id;'.format(table, key_str, value_str)

        
        cur.execute(insert_command)
        id = cur.fetchone()[0]
        
        if self.connection is None:
            con.commit()
            con.close()
        return id

        
    def update(self, id, values, key_names='all'):
        con = self.connection or self._connect()
        self._initialize(con)
        cur = con.cursor()

        key_str, value_str = get_key_value_str(values)

        update_command = 'UPDATE reaction SET ({}) = ({}) WHERE id = {};'\
            .format(key_str, value_str, id)


        cur.execute(update_command)
        #id = cur.fetchone()[0]
        if self.connection is None:
            con.commit()
            con.close()
        return id

    def update_publication(self, pub_dict, authorlist, year):
        con = self.connection or self._connect()
        self._initialize(con)
        cur = con.cursor()
        #SELECT jsonb_set('{"a":[null,{"b":[1,2]}]}', '{a,1,b,1000}', jsonb '3', true)        
        key0 = pub_dict.keys()[0]
        ids = []
        import json

        update_command = \
        """UPDATE reaction SET 
        publication = '{}'
        WHERE 
        publication -> 'authors' = '{}' and year = {} returning id;"""\
            .format(json.dumps(pub_dict), json.dumps(authorlist), year)
            #.format(key_str, value_str, id)


        #jsonb_set(publication, '{{{}}}', '{}' || '{}') 
        cur.execute(update_command)

        id = cur.fetchone()[0]
        if self.connection is None:
            con.commit()
            con.close()
        
        return id
    
    def delete(self, authorlist, year, doi=None):
        con = self.connection or self._connect()
        self._initialize(con)
        cur = con.cursor()
        if doi is None:
            delete_command = \
                """DELETE from reaction 
                WHERE 
                publication -> 'authors' = '{}' and year = {};""".format(authorlist, year)
        cur.execute(delete_command)
        count = cur.fetchone()[0]
        if self.connection is None:
            con.commit()
            con.close()

        return count

    def transfer(self, filename_sqlite, start_id=1, write_ase=True,
                 write_publication=True, write_reaction=True):
        con = self.connection or self._connect()
        self._initialize(con)
        cur = con.cursor()

        import ase
        import os
        from ase.db import *
        from ase.utils import plural
        password = os.environ['DB_PASSWORD']
        server_name = "postgres://catappuser:{}@catappdatabase.cjlis1fysyzx.us-west-1.rds.amazonaws.com:5432/catappdatabase".format(password)
        nkvp = 0
        nrows = 0
        if write_ase:
            db = ase.db.connect(filename_sqlite)
            with ase.db.connect(server_name, type='postgresql') as db2:
                for row in db.select():#'', sort=args.sort):cd
                    kvp = row.get('key_value_pairs', {})
                    nkvp -= len(kvp)
                    # kvp.update(add_key_value_pairs)
                    nkvp += len(kvp)
                    db2.write(row, data=row.get('data'), **kvp)
                    nrows += 1

                # print('Inserted %s' % plural(nrows, 'row'))
        
        from cathubsqlite import CathubSQLite
        db = CathubSQLite(filename_sqlite)
        con_lite = db._connect()
        cur_lite = con_lite.cursor()

        # write publication
        Npub = 0
        Npubstruc = 0
        if write_publication:
            try:
                npub = db.get_last_pub_id(cur_lite)
            except:
                npub = 1
            for id_lite in range(1, npub+1):
                Npub += 1
                row = db.read(id=id_lite, table='publication')
                if len(row) == 0:
                    continue
                values = row[0]
                pid, pub_id = self.write_publication(values)

            # Publication structures connection
            cur_lite.execute("""SELECT * from publication_system;""")
            rows = cur_lite.fetchall()
            for row in rows:
                Npubstruc += 1
                values= row[:]
                key_str, value_str = get_key_value_str(values,
                                                       table='publication_system')       
                insert_command = 'INSERT INTO publication_system ({}) VALUES ({}) ON CONFLICT DO NOTHING;'.format(key_str, value_str)
                
                cur.execute(insert_command)
                # self.write(values, table='publication_system')
            con.commit()
            
        Ncat = 0
        Ncatstruc = 0

        if write_reaction:
            n = db.get_last_id(cur_lite)
            select_ase = """SELECT * from reaction_system where id={};"""
            for id_lite in range(start_id, n+1):
                row = db.read(id_lite)
                if len(row) == 0:
                    continue
                values = row[0]

                id = self.check(values[1], values[7]) # values[5], values[6], 
                if id is not None:
                    print 'Allready in reaction db with row ied = {}'.format(id)
                    id = self.update(id, values)
                else:
                    Ncat += 1
                    id = self.write(values)
                    print 'Written to reaction db row id = {}'.format(id)

                cur_lite.execute(select_ase.format(id_lite))
                rows = cur_lite.fetchall()
                for row in rows:
                    Ncatstruc += 1

                    values = list(row)

                    values[2] = id
                    key_str, value_str = get_key_value_str(values,
                                                           table='reaction_system')
                    insert_command = 'INSERT INTO reaction_system ({}) VALUES ({}) ON CONFLICT DO NOTHING;'.format(key_str, value_str)


                    cur.execute(insert_command)
                
                con.commit() # Commit reaction_system for each row

        for statement in tsvector_update:
            cur.execute(statement)
                
        if self.connection is None:
            con.commit()
            con.close()

        print 'Inserted into:'
        print '  systems: {}'.format(nrows)
        print '  publication: {}'.format(Npub)
        print '  publication_system: {}'.format(Npubstruc)
        print '  reaction: {}'.format(Ncat)
        print '  reaction_system: {}'.format(Ncatstruc)
            
    def check(self, chemical_composition, reaction_energy):#reactants, products, reaction_energy):
        con = self.connection or self._connect()
        self._initialize(con)
        cur = con.cursor()
        statement = \
        """SELECT id 
        FROM reaction WHERE 
        (chemical_composition,  reaction_energy) = 
        ('{}', {})""".format(chemical_composition, reaction_energy)
        #argument = [reaction_energy]
        cur.execute(statement)
        rows = cur.fetchall()
        if len(rows) > 0:
            id = rows[0][0]
        else:
            id = None
        return id


    def publication_status(self):
        con = self.connection or self._connect()
        self._initialize(con)
        cur = con.cursor()

        select_statement = \
        """SELECT distinct publication
        FROM reaction WHERE 
        publication ->> 'doi' is null
        OR
        publication -> 'doi' is null;"""
        cur.execute(select_statement)
        pubs = cur.fetchall()

        return pubs

        
def get_key_value_str(values, table='reaction'):
    key_str = {'reaction': 'chemical_composition, surface_composition, facet, sites, reactants, products, reaction_energy, activation_energy, dft_code, dft_functional, username, pub_id',
               'publication': 'pub_id, title, authors, journal, volume, number, pages, year, publisher, doi, tags',
               'reaction_system': 'name, ase_id, reaction_id',
               'publication_system': 'ase_id, pub_id'}

    start_index = 1
    if table == 'publication_system' or table == 'reaction_system':
        start_index = 0
    value_str = "'{}'".format(values[start_index])
    for v in values[start_index+1:]:
        if isinstance(v, unicode):
            v = v.encode('ascii','ignore')
        if v is None or v == '':
            value_str += ", {}".format('NULL')
        elif isinstance(v, str):
            value_str += ", '{}'".format(v)
        else:
            value_str += ", {}".format(v)
        
    return key_str[table], value_str