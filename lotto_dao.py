import psycopg2

class LottoryConnection(object):

    def __init__(self):
        self.host="3.209.12.17"
        self.port=5432
        self.username="spenser"
        self.password="lolwut"
        self.dbname="wormbot_test"


    def __enter__(self):
        try:
            self.connection = psycopg2.connect(user=self.username,
                                                password=self.password,
                                                host=self.host,
                                                port=self.port,
                                                database=self.dbname
                                                )
        except(Exception, psycopg2.Error) as error:
            print("Error connecting to DB ", error)
        return self.connection

    def __exit__(self, type, value, traceback):
        self.connection.close()

def initialize_tables():
    table_data = {'member':{'user_id':'BIGINT PRIMARY KEY',
                        'balance':'BIGINT DEFAULT 0',
                        'daily_timestamp': 'TIMESTAMP DEFAULT NULL',
                        'cock': 'INT DEFAULT -1'
                        },
                  'ticket':{'ticket_id':'SERIAL PRIMARY KEY',
                        'ticket_value':'VARCHAR (255)',
                        'lottory_id':'INT',
                        'user_id':'BIGINT'
                        },
                  'lottory':{'lottory_id':'SERIAL PRIMARY KEY',
                        'jackpot':'INT DEFAULT 0',
                        'income': 'INT DEFAULT 0',
                        'outflow': 'INT DEFAULT 0'
                        },
                  }

    with LottoryConnection() as conn:
        curr = conn.cursor()
        for table_name, column_data in table_data.items():
            columns = []

            for column_name, column_type in column_data.items():
                columns.append('{cn} {ct}'.format(cn=column_name, ct=column_type))

            column_sql = '({})'.format(', '.join(columns))
            sql = 'CREATE TABLE IF NOT EXISTS {tn} {ts};'.format(tn=table_name, ts=column_sql)

            curr.execute(sql)
        conn.commit()

def add_lottory(jackpot=0):
    with LottoryConnection() as conn:
        curr = conn.cursor()
        sql = 'INSERT INTO lottory (jackpot) VALUES ({jp});'.format(jp=jackpot)
        curr.execute(sql)
        conn.commit()

def get_lottory_jackpot_prog(lottory_id):
    with LottoryConnection() as conn:
        curr = conn.cursor()
        get_lottory = 'SELECT jackpot FROM lottory WHERE lottory_id = {id};'.format(id=lottory_id)
        curr.execute(get_lottory)
        lottory_jackpot = curr.fetchone()
        return lottory_jackpot[0]

def modify_lottory_jackpot_prog(lottory_id, amount):
    with LottoryConnection() as conn:
        curr = conn.cursor()
        get_balance_sql = 'SELECT jackpot FROM lottory WHERE lottory_id = {};'.format(lottory_id)
        curr.execute(get_balance_sql)
        current_balance = curr.fetchone()[0]
        new_balance = current_balance + amount
        set_balance_sql = 'UPDATE lottory SET jackpot={} WHERE lottory_id={}'.format(new_balance, lottory_id)
        curr.execute(set_balance_sql)
        conn.commit()
        return new_balance

def update_lottory_stats(lottory_id, income, outflow):
    with LottoryConnection() as conn:
        curr = conn.cursor()
        sql = 'UPDATE lottory SET income={ic}, outflow={of} WHERE lottory_id={ld};'.format(ld=lottory_id, ic=income, of=outflow)
        curr.execute(sql)
        conn.commit()

def get_lottory_stats(lottory_id=None):
    with LottoryConnection() as conn:
        curr = conn.cursor()
        lottory_id_sql = '' if lottory_id is None else ' WHERE lottory_id={}'.format(lottory_id)
        sql = 'SELECT income, outflow FROM lottory{};'.format(lottory_id_sql)
        curr.execute(sql)
        return curr.fetchall()


def add_user(user_id):
    with LottoryConnection() as conn:
        curr = conn.cursor()
        add_user = 'INSERT INTO member (user_id) VALUES ({id}) ON CONFLICT DO NOTHING;'.format(id=user_id)
        curr.execute(add_user)
        conn.commit()

def get_user(user_id=None):
    with LottoryConnection() as conn:
        curr = conn.cursor()
        one_user = '' if user_id is None else 'WHERE user_id={}'.format(user_id)
        get_user_sql = 'SELECT user_id FROM member{};'.format(one_user)
        curr.execute(get_user_sql)
        return curr.fetchall()

def add_ticket_to_user(ticket_list, lottory_id, user_id):
    with LottoryConnection() as conn:
        batch_size = 100000
        curr=conn.cursor()
        add_ticket_sql = 'INSERT INTO ticket (ticket_value, lottory_id, user_id) VALUES'
        for n in range(0, len(ticket_list), batch_size):
            values_list = list(map(lambda x: (str(x), lottory_id, user_id), ticket_list[n:n+batch_size]))
            argument_string = ",".join(str(x) for x in values_list)
            curr.execute("{}{}".format(add_ticket_sql, argument_string))
            conn.commit()

def get_user_balance(user_id):
    with LottoryConnection() as conn:
        curr = conn.cursor()
        get_balance_sql = 'SELECT balance FROM member WHERE user_id = {};'.format(user_id)
        curr.execute(get_balance_sql)
        return curr.fetchone()[0]

def modify_user_balance(user_id, amount):
    with LottoryConnection() as conn:
        curr = conn.cursor()
        get_balance_sql = 'SELECT balance FROM member WHERE user_id = {};'.format(user_id)
        curr.execute(get_balance_sql)
        current_balance = curr.fetchone()[0]
        new_balance = current_balance + int(round(amount))
        set_balance_sql = 'update member SET balance={} WHERE user_id={};'.format(new_balance, user_id)
        curr.execute(set_balance_sql)
        conn.commit()
        return new_balance

def get_current_lottory():
    with LottoryConnection() as conn:
        curr = conn.cursor()
        get_lotto_sql = 'SELECT * FROM lottory ORDER BY lottory_id DESC LIMIT 1;'
        curr.execute(get_lotto_sql)
        return curr.fetchone()[0]

def get_lottory_tickets(lottory_id):
        with LottoryConnection() as conn:
            curr = conn.cursor()
            get_tickets_sql = 'SELECT ticket_value, user_id FROM ticket WHERE lottory_id={};'.format(lottory_id)
            curr.execute(get_tickets_sql)
            return curr.fetchall()

def get_user_tickets(user_id, lottory_id=None):
    with LottoryConnection() as conn:
        curr = conn.cursor()
        ld_sql = ' AND lottory_id = {ld}'.format(ld=lottory_id) if lottory_id is not None else ''
        get_ticket_sql = 'SELECT ticket_value FROM ticket WHERE user_id = {id}{ld};'.format(id=user_id, ld=ld_sql)
        curr.execute(get_ticket_sql)
        tickets = curr.fetchall()
        output = []
        for ticket in tickets:
            output.append(ticket[0])
        return output

def get_cock_status(user_id=None):
    with LottoryConnection() as conn:
        curr = conn.cursor()
        user_sql = '' if user_id is None else 'WHERE user_id={}'.format(user_id)
        get_cock_sql = 'SELECT cock FROM member {} ORDER BY cock DESC;'.format(user_sql)
        curr.execute(get_cock_sql)
        if user_id is None:
            return curr.fetchall()
        else:
            return curr.fetchone()[0]

def set_cock_status(user_id, status):
    with LottoryConnection() as conn:
        curr = conn.cursor()
        set_cock_sql = 'update member SET cock={} WHERE user_id={};'.format(status, user_id)
        curr.execute(set_cock_sql)
        conn.commit()

def get_config(param):
    with LottoryConnection() as conn:
        curr = conn.cursor()
        sql = "SELECT value FROM config WHERE param='{}';".format(param)
        curr.execute(sql)
        return curr.fetchone()[0]
