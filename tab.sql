CREATE TABLE conversation (.
con_id SERIAL NOT NULL,
con_chat_id INT NOT NULL,
con_stage_id TEXT NOT NULL,
con_config_path VARCHAR(255)  NOT NULL,
con_agent_name VARCHAR(255) NOT NULL,
con_message TEXT NULL,
create_dat TIMESTAMP NOT NULL,
create_usr VARCHAR(30) NOT NULL,
modify_dat TIMESTAMP NOT NULL,
modify_usr VARCHAR(30) NOT NULL,
PRIMARY KEY(con_id) );
