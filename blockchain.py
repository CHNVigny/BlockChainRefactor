import hashlib
import json
from time import time
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse
from uuid import uuid4
from queue import Queue
import requests
from flask import Flask, jsonify, request
import pysnooper


class Blockchain:
    def __init__(self):
        # self.__current_votes = Queue()
        self.__chain = []
        self.__nodes = set()
        self.__candidates = set()
        # self._es_block = 0

        # 创建创世块
        # self.new_block(previous_hash='1', proof=100)

    @property
    def chain(self) -> List:
        return self.__chain

    @property
    def candidates(self) -> Set:
        return self.__candidates

    def getblock(self, index: int) -> Dict[str, Any]:
        if index >= len(self.__chain) or index < -len(self.__chain):
            return None
        else:
            return self.__chain[index]

    # @staticmethod
    def read_file_list(self, filename: str = 'candidates.txt', mode: str = 'r', encoding: str = 'UTF-8') -> str:
        """
        read candidate file
        :param fileName:候选人名单（默认candidates.txt）
        :param mode:读写方式（默认只读）
        :param encoding:文件编码（默认UTF-8）
        :return:候选人列表
        """
        candidates = set()
        result = {}
        f = open(file=filename, mode=mode, encoding=encoding)
        candidateindex = 1
        for eachLine in f.readlines():
            line = eachLine.strip().replace('\n', '')
            candidates.add(line)
        self.__candidates = candidates
        for cadidate in candidates:
            result[str(candidateindex)] = cadidate
            candidateindex += 1
        # print("candidates " + json.dumps(result))
        f.close()
        return json.dumps(result)

    def send_candidates(self):
        """
        通过创建创世块的方法宣布候选人。
        :return:
        """
        candidates = self.read_file_list()
        # print("candidates "+candidates)
        self.create_foundation_block(previous_hash='1', proof=100, candidates=candidates)

    def register_node(self, address: str) -> None:
        """
        Add a new node to the list of __nodes

        :param address: Address of node. Eg. 'http://192.168.0.5:5000'
        """

        parsed_url = urlparse(address)
        self.__nodes.add(parsed_url.netloc)

    def valid_chain(self, chain: List[Dict[str, Any]]) -> bool:
        """
        验证链的合法性

        :param chain: 一个链
        :return: 合法, 否则False
        """

        last_block = chain[0]  # 初始化
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # 检查前一个块的哈希值是否正确
            if block['previous_hash'] != self.hash(last_block):
                return False

            # 检查proof值是否合法
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False
            last_block = block
            current_index += 1
        return True

    def resolve_conflicts(self) -> bool:
        """
        共识算法解决冲突
        使用网络中最长的链.
        :return:  如果链被取代返回 True, 否则为False
        """
        neighbours = self.__nodes
        new_chain = None
        max_length = len(self.__chain)
        # 抓取并验证我们保存的所有节点的chain
        for node in neighbours:
            response = requests.get(f'http://{node}/__chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                # 检查链的长度以及合法性
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        # 有更长的链时用更长的链替代我们的链
        if new_chain:
            self.__chain = new_chain
            return True
        return False

    def create_foundation_block(self, proof: int, previous_hash: str, candidates: str) -> Dict[str, Any]:
        """
        创建创世块
        :param previous_hash: 输入一个哈希值
        :param proof: 创世块的proof
        :param candidates:
        :return:
        """
        return self.new_block(proof, previous_hash, candidates=candidates, foundation="true")

    def new_block(self, proof: int, previous_hash: Optional[str], vote: str = None, candidates: str = None,
                  foundation="false", ) -> None:
        """
        生成新块

        :param proof: 由工作量证明算法计算出来的proof
        :param previous_hash: 前一个块的Hash
        :param vote: 投的票
        :return: 新块
        """
        if foundation == "true":
            if len(self.__chain) != 0:
                print("Foundation Block Exists Already!")
                return
            else:
                print("candidates " + candidates)
                block = {
                    'index': len(self.__chain) + 1,
                    'timestamp': time(),
                    'candidates': str(candidates),
                    'proof': proof,
                    'previous_hash': previous_hash or self.hash(self.__chain[-1]),
                }
                self.__chain.append(block)
                print(self.__chain)
                return block
        else:
            block = {
                'index': len(self.__chain) + 1,
                'timestamp': time(),
                'vote': vote,  # self.__current_votes.get(),
                'proof': proof,
                'previous_hash': previous_hash or self.hash(self.__chain[-1]),
            }
            # block['hash'] = self.hash(block)

            # 重置交易列表
            # elf.current_votes = []

            self.__chain.append(block)
            print(self.chain)
            return block

    def new_vote_block(self, vote: str, factor: str) -> int:
        """
        生成新块

        :param proof: 由工作量证明算法计算出来的proof
        :param previous_hash: 前一个块的Hash
        :return: 新块
        """
        last_block = blockchain.last_block
        previous_hash = self.hash(last_block)
        last_proof = last_block['proof']
        proof = blockchain.proof_of_work(last_proof)
        block = {
            'index': len(self.__chain) + 1,
            'timestamp': time(),
            'vote': vote,  # self.__current_votes.get(),
            'factor': factor,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.__chain[-1]),
        }
        # block['hash'] = self.hash(block)

        # 重置交易列表
        # elf.current_votes = []
        self.__chain.append(block)
        return len(self.__chain)

    def new_vote(self, sender: str, recipient: str, vote_hash: str) -> int:
        """
        生成新的投票信息加入到队列中
        :param vote:
        :return:
        """
        vote = {
            'sender': sender,
            'recipient': recipient,
            'vote_hash': vote_hash,
        }
        self.__current_votes.put(vote)
        return self.last_block['index'] + self.__current_votes.qsize()

    def sync_candidates(self) -> bool:
        """
        设置候选人
        :return:
        """
        if len(self.__chain):
            self.__candidates = self.__chain[0].candidates
            return True
        else:
            print(f'no block yet')
            return False

    @property
    def last_block(self) -> Dict[str, Any]:
        print(str(self.__chain))
        return self.__chain[-1]

    @staticmethod
    def hash(block: Dict[str, Any]) -> str:
        """
        生成块的 SHA-256 hash值

        :param block: Block
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_proof: int) -> int:
        """
        简单的工作量证明:
         - 查找一个 p' 使得 hash(pp') 以4个0开头
         - p 是上一个块的证明,  p' 是当前的证明
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof: int, proof: int) -> bool:
        """
        验证证明: 是否hash(last_proof, proof)以4个0开头

        :param last_proof: 前一个区块的proof
        :param proof: 要验证的proof
        :return: 正确返回True, 否则返回False.
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


# Instantiate the Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()
blockchain.send_candidates()
print(str(blockchain.getblock(-1)))
print(blockchain.hash(blockchain.getblock(0)))

@pysnooper.snoop('./log/file.log')
def new_vote(vote: str) -> None:
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)
    blockchain.new_block(proof, None, vote,)#这里的previous_hash这个参数完全可以穿一个None，可以自动计算的。

@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # 给工作量证明的节点提供奖励.
    # 发送者为 "0" 表明是新挖出的币
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Forge the new Block by adding it to the __chain
    block = blockchain.new_block(proof, None)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    print(values)
    # 检查POST数据
    required = ['vote', 'factor']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = blockchain.new_vote_block(values['vote'], values['factor'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/__chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/__nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    print(values)
    print(type(values))
    nodes = values.get('__nodes')

    if nodes is None:
        return "Error: Please supply a valid list of __nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New __nodes have been added',
        'total_nodes': list(blockchain.__nodes),
    }
    return jsonify(response), 201


@app.route('/__nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our __chain was replaced',
            'new_chain': blockchain.__chain
        }
    else:
        response = {
            'message': 'Our __chain is authoritative',
            '__chain': blockchain.__chain
        }

    return jsonify(response), 200


if __name__ == '__main__':
    # from argparse import ArgumentParser
    #
    # parser = ArgumentParser()
    # parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    # args = parser.parse_args()
    # port = args.port
    #
    # app.run(host='127.0.0.1', port=port)
    while(True):
        vote = input("请输入候选人：")
        if vote in blockchain.candidates:
            start = time()
            new_vote(vote)
            end = time()
            t = end - start
            print("执行时间：" + str(t))
        elif vote == "exit":
            print("投票结束！")
            break
        else:
            print("无效候选人！")

