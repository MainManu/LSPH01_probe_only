import time


class error_log:
    def __init__(self, tag:str="",  file:str="error.log") -> None:
        self.tag = tag
        self.file = file
    def error(self, message:str, context:str=""):
        message = f"ERROR: {message}"
        self.log(message, context)
    def warning(self, message:str, context:str=""):
        message = f"WARNING: {message}"
        self.log(message, context)
    def info(self, message:str, context:str=""):
        message = f"INFO: {message}"
        self.log(message, context)
    def log(self, message:str, context:str=""):
        try:
            with open(self.file, "a") as f:
                if self.tag == "":
                    f.write(f"{time.asctime()}:{message} {context}\n")
                else:
                    f.write(f"[{self.tag}]{time.asctime()}:{message} {context}\n")
        except FileNotFoundError:
            print("No error log found")
        except Exception as e:
            print(f"Unknown error: {e}")

if __name__ == "__main__":
    err_log = error_log(tag="test", file="test_log.log")
    err_log.log("test message", "test context")
