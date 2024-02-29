import logging
import os
import traceback
try:
    import re
    import sys
    import threading
    import tkinter.simpledialog
    import tkinter.messagebox
    from tkinter import *
    from api_server import server
    from api_client import *
    import utils
    from security import WrongPassword

    window = Tk()
    window.title("The Ark")
    window.geometry("600x400")
    window.resizable(width=False, height=False)

    contact_list = StringVar()
    contacts_frame = Frame(window, width=400, height=400)
    contacts_frame.pack(side=LEFT)
    contacts_l = Listbox(contacts_frame, listvariable=contact_list, width=30, height=25)
    contacts_l.pack(side=LEFT)

    contacts_scrollbar = Scrollbar(contacts_frame, orient="vertical", command=contacts_l.yview)
    contacts_scrollbar.pack(side=RIGHT, fill=Y)
    contacts_l['yscrollcommand'] = contacts_scrollbar.set

    chat_list = StringVar()
    chat_frame = Frame(window)
    chat_frame.pack(side=LEFT)
    send_message_frame = Frame(chat_frame)
    send_message_frame.pack(side=BOTTOM)

    def send(event=None):
        try:
            global selected_chat
            text = chat_entry.get()
            if text != "" and text is not None:
                #print(selected_chat)
                contact = server.get_contacts()[selected_chat]
                client = Client(contact, server.key)
                client.connect()
                threading.Thread(target=client.send_message, args=(text, )).start()
                server.add_message(contact, text, selfsent=True)
                chat_entry.delete(0, END)
                threading.Thread(target=change_chat, args=(None, True)).start()
        except Exception:
            logging.error(traceback.format_exc())


    chat_send_button = Button(send_message_frame, text="send", width=5, state=DISABLED, command=send)
    chat_send_button.pack(side=RIGHT, expand=1)
    chat_entry = Entry(send_message_frame, width=58, state=DISABLED)
    chat_entry.pack(side=LEFT, expand=1)
    chat_l = Listbox(chat_frame, listvariable=chat_list, width=63, height=400, selectmode=SINGLE)
    chat_l.pack(side=LEFT)

    chat_scrollbar = Scrollbar(chat_frame, orient="vertical", command=chat_l.yview)
    chat_scrollbar.pack(side=RIGHT, fill=Y)
    chat_l['yscrollcommand'] = chat_scrollbar.set

    selected_chat = None
    chat_update_called = False

    name_pattern = re.compile("[A-Za-z0-9]+")

    def new_contact_button_command():
        to_add = new_contact_address_2.get()
        if to_add != "":
            try:
                client = Client(to_add, server.key)
                client.connect()
                contact_name = tkinter.simpledialog.askstring("Adding contact", "Almost done!\nName the contact")
                server.add_contact(contact_name, to_add)

                new_contact_window.destroy()
                l = list(server.get_contacts())
                l.append("----------------------------------------")
                l.append("Add contact")

                # noinspection PyTypeChecker
                contact_list.set(l)
            except Exception:
                tkinter.messagebox.showerror("Error adding contact", "Failed adding contact, contact should be online while adding proccess")

    def save_to_clipboard(event):
        window.clipboard_clear()
        window.clipboard_append(server.service_host)
        window.update()
    def new_contact():
        global new_contact_address_1
        global new_contact_address_2
        global new_contact_window
        new_contact_window = Toplevel(window, height=300)
        new_contact_window.resizable(width=False, height=False)
        new_contact_label_1 = Label(new_contact_window, text="Give this address to a contact who you would like to add")
        new_contact_label_1.pack()
        new_contact_address_1 = Entry(new_contact_window)
        new_contact_address_1.insert(0, server.service_host)
        new_contact_address_1.config(state='disabled', width=0)
        new_contact_address_1.pack()
        #print(new_contact_address_1.winfo_width())
        new_contact_address_1.bind('<Double-1>', save_to_clipboard)
        new_contact_label_2 = Label(new_contact_window, text="Enter here your contact's address")
        new_contact_label_2.pack()
        new_contact_address_2 = Entry(new_contact_window, width=55)
        new_contact_address_2.pack()
        new_contact_button = Button(new_contact_window, text="Add contact", command=new_contact_button_command)
        new_contact_button.pack()


    def change_chat(event=None, newmessage=False):
        global selected_chat
        global chat_update_called
        if not chat_update_called:
            try:
                chat_update_called = True
                #logging.info("Updating chat list...")
                #print(newmessage, selected_chat)
                if not newmessage:
                    selected_chat = contacts_l.selection_get()
                if selected_chat != "----------------------------------------" and selected_chat != "Add contact":
                    #logging.info("Getting messages...")
                    messages = server.get_messages(selected_chat)
                    #print(messages)
                    mes = []
                    #logging.info("Processing messages...")
                    for i in messages:
                        if i['author'] != "":
                            try:
                                t = f"{i['timestamp']} - {i['author']}: {i['text'].decode()}"
                            except AttributeError:
                                t = f"{i['timestamp']} - {i['author']}: {i['text']}"
                        else:
                            try:
                                t = f"{i['timestamp']} - {server.name}: {i['text'].decode()}"
                            except AttributeError:
                                t = f"{i['timestamp']} - {server.name}: {i['text']}"
                        t = [t[i:i + 68] for i in range(0, len(t), 68)]
                        for d in t:
                            mes.append(d)

                    # noinspection PyTypeChecker
                    #print(mes)
                    #logging.info("Updating...")
                    #print(mes)
                    chat_list.set(mes)
                    #logging.info("Updating done!")
                    if not newmessage:
                        chat_send_button.config(state=NORMAL)
                        chat_entry.config(state=NORMAL)
                    #chat_l.config(width=0)
                elif selected_chat == "Add contact":
                    new_contact()
                chat_update_called = False
            except Exception:
                logging.error(traceback.format_exc())

    if not os.path.exists(utils.database_path):
        # first start
        name = ""
        password = ""
        while name == "":
            name = tkinter.simpledialog.askstring("Weclome to the Ark!", "Welcome to The Ark!\nEnter your username that other people will see, it should use only letters and numbers")
            if not re.match(name_pattern, name):
                name = ""
        if name is None:
            sys.exit()
        while password == "":
            password = tkinter.simpledialog.askstring("Weclome to the Ark!", "Now create new password.\nIt will be used to encrypt your data, so if you lose it, there will be no way to recover it!")
        if password is None:
            sys.exit()
        server.key = password
        server.start(name=name)
    else:
        password = ""
        text = "Enter your password"
        while password == "":
            password = tkinter.simpledialog.askstring("Weclome to the Ark!", text)
            try:
                if password is not None:
                    server.key = password
                    testing_storage = Storage(utils.database_path, password)
                    testing_storage.read()
                    server.start()
            except WrongPassword:
                password = ""
                text = "Wrong password, please try again."
        if password is None:
            sys.exit()

    l = list(server.get_contacts())
    l.append("----------------------------------------")
    l.append("Add contact")

    # noinspection PyTypeChecker
    contact_list.set(l)
    contacts_l.bind('<Double-1>', change_chat)
    chat_entry.bind('<Return>', send)
    server.on_message_listener = change_chat
    def on_closing():
        sys.exit()

    window.protocol("WM_DELETE_WINDOW", on_closing)

    window.mainloop()
except Exception:
    logging.error(traceback.format_exc())
