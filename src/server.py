#  Created by Artem Manchenkov
#  artyom@manchenkoff.me
#
#  Copyright © 2019
#
#  Сервер для обработки сообщений от клиентов
#
#  Ctrl + Alt + L - форматирование кода
#
from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory, connectionDone
from twisted.protocols.basic import LineOnlyReceiver


class ServerProtocol(LineOnlyReceiver):
    factory: 'Server'
    login: str = None
    history = []
    # def connectionMade(self):
    # Потенциальный баг для внимательных =) Добавляем пользователя только после проверки на уникальность
    # self.factory.clients.append(self)

    def connectionLost(self, reason=connectionDone):
        if self in self.factory.clients:
            self.factory.clients.remove(self)

    def already_logged(self):
        is_logged = False
        for user in self.factory.clients:
            if self.login == user.login:
                is_logged = True
        return is_logged

    def send_history(self):
        for message in self.history:
            self.sendLine(message.encode())

    def lineReceived(self, line: bytes):
        content = line.decode()

        if self.login is not None:
            content = f"Message from {self.login}: {content}"
            if len(self.history) >= 10:
                del self.history[0]
            self.history.append(content)  # запись сообщения в историю
            for user in self.factory.clients:
                if user is not self:
                    user.sendLine(content.encode())
        elif content.startswith("login:"):
            self.login = content.replace("login:", "")
            if self.already_logged():  # проверка на уникальность
                self.sendLine(f"Логин '{self.login}' занят, попробуйте другой".encode())
                self.login = None
                self.connectionLost()
            else:
                self.factory.clients.append(self)
                self.sendLine("Welcome!".encode())
                self.send_history()  # отправка последних 10-ти сообщений
        else:
            self.sendLine("Invalid login".encode())


class Server(ServerFactory):
    protocol = ServerProtocol
    clients: list

    def startFactory(self):
        self.clients = []
        print("Server started")

    def stopFactory(self):
        print("Server closed")


reactor.listenTCP(1234, Server())
reactor.run()
