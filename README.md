PolyNOM — Polypheny Native Object Mapper

**PolyNOM** is a powerful Python-based object mapping layer designed to work seamlessly with [Polypheny](https://polypheny.com), the flexible and distributed data management platform. It leverages the [`Polypheny Connector Python`](https://github.com/polypheny/Polypheny-Connector-Python) to simplify the development process by providing automatic object mapping, schema migration, and changelog tracking.

PolyNOM allows developers to work with Python classes and objects, while automatically handling the communication and translation with a Polypheny instance — either via Docker or direct host/port configuration.

---

## 🚀 Features

- ✅ **Object Mapping**  
  Map native Python classes to Polypheny collections with minimal boilerplate.

- 🔄 **Automatic Schema Migration**  
  Define your data model in Python and let PolyNOM handle schema creation and updates on the fly.

- 📜 **Changelog Support**  
  Track and log structural changes applied to your schema over time for better versioning and auditing.

- 🐳 **Automatic Docker Deployment**  
  Easily spin up a local Polypheny instance using Docker in one command.

- ⚡ **Fast and Lightweight**  
  Built with simplicity and performance in mind, ideal for rapid development and prototyping.

